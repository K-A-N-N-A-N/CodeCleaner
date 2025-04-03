from transformers import AutoModel, AutoTokenizer
from openai import OpenAI

client = OpenAI()

# Load the T5-based model
checkpoint = "D:/CodeCleaner/Main/CodeCleaner/backend/summaryt5"
tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True)

def extract_code_from_markdown(code_text):
    """Helper function to extract code from markdown code blocks."""
    lines = code_text.split("\n")
    inside_code_block = False
    extracted_code = []

    for line in lines:
        if line.strip().startswith("```java"):
            inside_code_block = True
            continue
        elif line.strip().startswith("```"):
            inside_code_block = False
            continue
        if inside_code_block:
            extracted_code.append(line)

    return "\n".join(extracted_code) if extracted_code else code_text

def rename_variables(java_code):
    """Step 1: Rename variables, functions, and classes to meaningful names."""
    prompt = f"""
    You are a code refactoring tool. Your task is to analyze the provided Java code and rename:
    1. Variables to meaningful names based on their purpose.
    2. Class names to something relevant to the program's functionality.
    3. Function names to describe their behavior.
    4. Do NOT add comments to the code.

    Do not hardcode specific names in the response; instead, infer meaningful names from the code's context.

    Here is the Java code:
    {java_code}

    Return the updated code, and preserve the structure and indentation.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in analyzing and refactoring Java code."},
            {"role": "user", "content": prompt}
        ]
    )

    renamed_code = completion.choices[0].message.content
    return extract_code_from_markdown(renamed_code)

def add_code_summaries(java_code):
    """Step 2: Add summaries and comments to the code."""
    lines = java_code.split("\n")
    brcount = 0
    max_level = 0
    comments_dict = {}

    # First pass: find maximum nesting level
    for line in lines:
        brcount += line.count('{')
        brcount -= line.count('}')
        if brcount > max_level:
            max_level = brcount

    # Second pass: generate summaries for each block
    for level in range(max_level):
        brcount = 0
        temp = ""
        line_number = 0
        start = False

        for line in lines:
            line_number += 1
            brcount += line.count('{')
            
            if brcount >= level + 1:
                if not start:
                    current_line = line_number
                temp += line + "\n"
                start = True
            elif start:
                if temp.strip():
                    input_ids = tokenizer(temp, return_tensors="pt").input_ids
                    generated_ids = model.generate(input_ids, max_length=20)
                    summary = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
                    
                    # Only add meaningful summaries
                    if not (summary.startswith("public void static ") or 
                           summary.startswith("public static ") or 
                           summary.startswith("function ") or 
                           summary.strip().endswith(";")):
                        comments_dict[current_line] = summary
                
                temp = ""
                start = False
            
            brcount -= line.count('}')

        # Handle the last block if any
        if temp.strip():
            input_ids = tokenizer(temp, return_tensors="pt").input_ids
            generated_ids = model.generate(input_ids, max_length=20)
            summary = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
            if not (summary.startswith("public static ") or 
                   summary.startswith("function ") or 
                   summary.strip().endswith(";")):
                comments_dict[1] = summary

    # Add comments to the code
    final_lines = []
    for i, line in enumerate(lines, 1):
        if i in comments_dict:
            final_lines.append(f"// {comments_dict[i]}")
        final_lines.append(line)

    final_code = "\n".join(final_lines)

    # Final summary check and correction
    prompt = f"""
    You are a code analyzing tool. Below given is a Java code with some comments added to it.
    - If and ONLY IF the comments are completely inaccurate, slightly alter the comment to provide better meaning.
    - If it is even vaguely accurate to what is being done in the code, do not alter it.
    - Do NOT add new comments where there aren't any.

    The code is given below:
    {final_code}

    Return the updated code, and preserve the structure and indentation.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in analyzing and refactoring Java code."},
            {"role": "user", "content": prompt}
        ]
    )

    final_code = completion.choices[0].message.content
    return extract_code_from_markdown(final_code)

def refactor_java_code(java_code):
    """Main function to refactor Java code and add a summary comment."""
    try:
        # Step 1: Generate summary using T5 model
        inputs = tokenizer(java_code, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(**inputs, max_length=150, num_beams=4, early_stopping=True)
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Step 2: Rename variables and refactor code
        refactored_code = rename_variables(java_code)
        
        # Step 3: Add summary as a comment at the start
        final_code = f"// {summary}\n\n{refactored_code}"
        
        return final_code
    except Exception as e:
        print(f"Error in refactoring: {e}")
        return java_code  # Return original code if refactoring fails 