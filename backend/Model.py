from transformers import AutoModel, AutoTokenizer
from openai import OpenAI
client = OpenAI()

#import torch, gc
checkpoint = "D:/CodeCleaner/Main/CodeCleaner/backend/summaryt5"
 # for GPU usage or "cpu" for CPU usage
tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True)
 #snippet for calling and activating the model 
def refactor_java_code(java_code):
    """
    Refactor Java code to rename non-meaningful variables, class names,
    and function names to meaningful ones based on context.
    """
    prompt = f"""
You are a code refactoring tool. Your task is to analyze the provided Java code and rename:
1. Variables to meaningful names based on their purpose.
2. Class names to something relevant to the program's functionality.
3. Function names to describe their behavior.

Do not hardcode specific names in the response; instead, infer meaningful names from the code's context.

Here is the Java code:
{java_code}

Return the updated code, and preserve the structure and indentation.
    """

    # Call the GPT model
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in analyzing and refactoring Java code."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the content of the first choice
    return completion.choices[0].message.content
java_code = """
public class PrimeNumbers {
    public static void main(String[] args) {
        int c = 0;
        for (int n = 2; n <= 50; n++) {
            boolean b = true;
            for (int i = 2; i <= Math.sqrt(n); i++) {
                if (n % i == 0) {
                    b = false;
                    break;
                }
            }
            
            if (b) {
                System.out.print(n + " ");
                c++;
            }
        }
        System.out.println("\nTotal primes: " + c);
    }
}
"""
refactored_code = refactor_java_code(java_code)
print("Refactored Java Code:\n")
print(refactored_code)
lines = refactored_code.split("\n")
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
# Save the output to Rename.java
with open("D:/CodeCleaner/Main/CodeCleaner/backend/Renamed.java", "w") as outfile:
    outfile.write("\n".join(extracted_code))

''' 
tok = RobertaTokenizer.from_pretrained('C:/Users/ASUS/Desktop/Code/cbert/u1/newtest-T5')
moda= T5ForConditionalGeneration.from_pretrained('C:/Users/ASUS/Desktop/Code/cbert/u1/newtest-T5')''' #model alt ver.

fname="D:/CodeCleaner/Main/CodeCleaner/backend/Renamed.java" # file locashun
output_fname = "D:/CodeCleaner/Main/CodeCleaner/backend/Summary.java"  # Output Java file

file1 = open(fname, 'r')
brcount=0
l=0
dict1={}
for line in file1:
    brcount +=line.count('{')
    brcount -=line.count('}')
    if brcount>l:
        l=brcount
file1.close()
for i in range(l):
    #print("==========level: ",i+1,"============")
    brcount=0
    file2 = open(fname, 'r')
    start=0
    temp=""
    lcount=0

    for line in file2:
        lcount+=1
        brcount +=line.count('{')
        if brcount>=i+1:
            if start!=1:
                tc=lcount
            temp+=line
            start=1
        elif start==1:
            input_ids = tokenizer(temp, return_tensors="pt").input_ids

            generated_ids = model.generate(input_ids, max_length=20)
            dtext = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
            
            if dtext.startswith("public static ") or dtext.startswith("function "):
                print("//#####")
            elif dtext.strip().endswith(";"):
                '''del tokenizer, model
                gc.collect()
                torch.cuda.empty_cache()
                tok = RobertaTokenizer.from_pretrained('C:/Users/ASUS/Desktop/Code/cbert/u1/newtest-T5')
                moda= T5ForConditionalGeneration.from_pretrained('C:/Users/ASUS/Desktop/Code/cbert/u1/newtest-T5')
                inp = tok(temp, return_tensors="pt").input_ids

                gens = moda.generate(inp, max_length=20)
                print("//",tok.decode(gens[0], skip_special_tokens=True))
                del tok, moda
                gc.collect()
                torch.cuda.empty_cache()
                tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
                model = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).to(device)'''

                #print("//>>>>>")
            else:
                #print(tc,"// ",dtext,"\n")
                dict1.update({tc: dtext})
            #print("++",temp)
            temp=""
            #print("----------------------------------------")
            start=0
        brcount -=line.count('}')
    if temp !="":
        
        input_ids = tokenizer(temp, return_tensors="pt").input_ids

        generated_ids = model.generate(input_ids, max_length=20)
        dtext = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        print("1 // ", dtext,"\n")

        dict1.update({1: dtext})
        print("**",temp,"**")
#        start=0
        temp=""
    file2.close() 
print(dict1)
with open(fname, "r") as src, open(output_fname, "w") as dest:
    for line_number, line in enumerate(src, start=1):  #line numbered from 1
        if line_number in dict1:
            line = line.rstrip() + "  // "+dict1[line_number] + "\n"  #Append comment
        dest.write(line)
print("\n===== Contents of the File w summary =====\n")
with open(output_fname, "r") as dest:
    for line in dest:
        print(line, end="") 