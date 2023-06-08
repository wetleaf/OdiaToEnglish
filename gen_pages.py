from pdf2image import convert_from_path
import os
pages = convert_from_path('Dictionaries/Odia.Dictionary.pdf')

if not(os.path.isdir("pages")):
    os.mkdir("pages")
    
for i in range(len(pages)):
    pages[i].save("pages/"+'page'+ str(i) +'.jpg', 'JPEG')