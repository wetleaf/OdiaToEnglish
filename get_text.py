import cv2 as cv
import numpy as np
import pytesseract
import os


missed_words = ["of",
                "or",
                "as",
                "a",
                "awe",
                "coot",
                "ah",
                "Christ",
                "eater",
                "an"
]

syntactic_categories = ["adjective",
                        "adverb",
                        "adposition",
                        "conjuction",
                        "coordinating conjunction",
                        "coordinating connective",
                        "correlative connective",
                        "determiner",
                        "interjection",
                        "intransitive verb",
                        "noun",
                        "preposition",
                        "pronoun",
                        "subordinating conjunction",
                        "subordinating connective",
                        "transitive verb",
                        "verb"
]
verlines = [[70,550],[570,1050],[1070,1550]]
can_come_in_odia_words = [40,41,44,45,46]
can_be_a_eng_word = [2918]

def horizontal_lines(img):
    row,col = img.shape
    header = 170
    footer = 2030
    lines = [header]
    thresh = int(0.8*col)
    for r in range(header,footer):
        count = 0
        for c in range(col):
            if (img[r][c]):
                count += 1
    
        if r < footer and count > thresh:
            if (r- 75 > lines[0]):
                lines.append(r-70)
                lines.append(r+5)
            else:
                lines[0]=r+5

    lines.append(footer)
    

    for i in range(len(lines)-1):

        if (lines[i+1] - lines[i] < 4):
            lines[i+1] = lines[i]
      
    lines = np.unique(lines)
    return lines


def language_detection(text):

  if text == "" or text == " " :
      return "None"

  for t in text:
      if not (ord(t) >=32 and ord(t) < 127) :
            return "ori"
  return "eng"

def get_lines(gray,relief ):
    row,col = gray.shape
    status = 0 # 0 show white lines are running 1 shows black
    contour_lines = [0]

    for i in range(row):

        if (status == 0):
            for j in range(col):

                if ( gray[i][j] ):
                    contour_lines.append(i)
                    
                    status = 1
                    break

            continue
        
        if (status == 1):

            for j in range(col):
                if (gray[i][j]):
                    break
            else:

                contour_lines.append(i)
                status = 0





    for i in range(len(contour_lines)-1):

        if (contour_lines[i+1] - contour_lines[i] < relief):
            contour_lines[i+1] = contour_lines[i]


    contour_lines.append(row)

    contour_lines = np.unique(contour_lines)
    new_contour_lines = []
    for i in range(0,len(contour_lines),2):
        space_start = contour_lines[i]
        space_end = contour_lines[i+1]
        new_contour_lines.append((space_end+space_start)//2)


    return new_contour_lines

def get_words(contour_lines,gray,relief):
    # column time
    row,col = gray.shape
    status = 0
    contour_words = []

    for idx in range(0,len(contour_lines)-1):
        start = contour_lines[idx]
        end = contour_lines[idx+1] + 1

        count = 0
        contour_words.append([start,end,0])
        for c in range(col):
            if status == 0:

                for r in range(start,end):
                    
                    if (gray[r][c]):
                        s,e,c2 = contour_words.pop()
                        contour_words.append([start,end,(c + c2)//2])
                        status = 1
                        break
                continue

            if status == 1:

                for r in range(start,end):

                    if (gray[r][c]):
                        count = 0
                        break

                else:
                    count += 1
                    if (count > relief):
                        status = 0
                        contour_words.append([start,end,c-relief])
                        count = 0

    for colidx in  range(0,len(contour_words)-1):
        ax1,x2,y1 = contour_words[colidx]
        bx1,x2,y2 = contour_words[colidx+1]
        if (ax1 != bx1):
            contour_words[colidx][2] = (col + y1)//2
    
    return contour_words

def isSus(text):

    for t in text:
        if ((ord(t) not in can_come_in_odia_words and (ord(t) >32 and ord(t) < 127)) or ord(t) in can_be_a_eng_word):
            return True
    return False

def process(t):
    temp = ""
    for i in t:
        if (i=='\n'):
            break
        temp += i
    
    i = 0
    while(i<len(temp) and temp[i] == " "):
        i += 1
    temp = temp[i:]
    i = len(temp)-1
    while(i>=0 and temp[i] ==" "):
        i -= 1
    temp = temp[:i+1]
    return temp

def generate_text(start,end,psm=3):
    
    text = []


    for pagenum in range(start,end+1):

        nimg = cv.imread("pages/page"+str(pagenum)+".jpg")
        img = nimg.copy()

        gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
        gray = cv.threshold(gray,0,255,cv.THRESH_BINARY | cv.THRESH_OTSU)[1]
        gray = 255 - gray

        # 0 for white and 255 for black
        row,col = gray.shape



        horlines = horizontal_lines(gray)

        for l in range(0,len(horlines),2):

            line1 = horlines[l]
            line2 = horlines[l+1]
            for v in verlines:
                crop_img = gray[line1:line2,v[0]:v[1]]
                # cv.imwrite("output/crop_img" + str(pagenum) + str(l)+".jpg",crop_img)
                lines = get_lines(crop_img,10)
                words = get_words(lines,crop_img,4)

                # draw_boxes(nimg[line1:line2,v[0]:v[1]],lines,words,pagenum + l )
                for colidx in  range(0,len(words)-1):
                    ax1,x2,y1 = words[colidx]
                    bx1,x2,y2 = words[colidx+1]
                    if (ax1 != bx1):
                        continue
                    x1 = ax1
                    word_img = crop_img[x1:x2+1,y1:y2+1]

                    options_1 = "-l {} --psm {}".format("ori",psm)
                    options_2 = "-l {} --psm {}".format("eng",psm)
                    t1 = pytesseract.image_to_string(word_img,config=options_1)[:-1]
                    t1 = process(t1)
                    t2 = pytesseract.image_to_string(word_img,config=options_2)[:-1]
                    t2 = process(t2)
                    if (t2 in missed_words or isSus(t1)):
                        temp = t2
                    else:
                        temp = t1

                    lang = language_detection(temp)


                    if lang != "None":
                        text.append([temp,lang])
    text = write_text(text)
        
    return text

def isPrefix(word):
    word = word.lower()
    for w in syntactic_categories:
        for i in range(min(len(w),len(word))):
            if w[i] != word[i] :
                break
        else:
            return True
    return False

# format
# lang1 lang1 lang2 

def write_text(text):
    updated_text = ""

    last_lang = "eng"

    for idx in range(len(text)):
        lang = text[idx][1]
        t = text[idx][0]

        if (last_lang == "ori" and lang=="eng"):

            j = idx
            l = lang
            word = ""
            while (l == "eng"):
                word += text[j][0]
                word += " "
                j += 1
                if (j < len(text)):
                    l = text[j][1]
                else:
                    break
            

            if (isPrefix(word)):
                updated_text += t + " "

            else:
                updated_text += "\n" + t + " "

            last_lang = "eng"
        elif (lang == "ori"):
            updated_text += t + " "

            last_lang = "ori"
        else:
            updated_text += t + " "

            last_lang = "eng"
    return updated_text

def draw_boxes(img,contour_lines,contour_words,count):
    newimg = img.copy()
    row,col = newimg.shape
    for idx in range(len(contour_lines)):
        cv.line(newimg,(0,contour_lines[idx]),(col,contour_lines[idx]),(0,255,0),1,8)

    for idx in range(len(contour_words)):
        cv.line(newimg,(contour_words[idx][2],contour_words[idx][0]),(contour_words[idx][2],contour_words[idx][1]),(255,0,0),1,8)
    
    if not (os.path.isdir("output")):
        os.mkdir("output")
    cv.imwrite("output/output"+str(count)+".png",newimg)



# output text from pages [start,end]
# counting starts from 0 
text = generate_text(start =6,end = 6,psm = 6) 

file = open("output.txt",'w')
file.write(text)
file.close()



