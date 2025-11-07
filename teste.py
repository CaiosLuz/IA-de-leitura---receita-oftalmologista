import cv2;
import pytesseract;

import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print("=======LENDO IMAGEM=========")

img = cv.imread('receita1.jpeg', cv.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check with os.path.exists()"
ret,thresh1 = cv.threshold(img,127,255,cv.THRESH_BINARY)
ret,thresh2 = cv.threshold(img,127,255,cv.THRESH_BINARY_INV)
ret,thresh3 = cv.threshold(img,127,255,cv.THRESH_TRUNC)
ret,thresh4 = cv.threshold(img,127,255,cv.THRESH_TOZERO)
ret,thresh5 = cv.threshold(img,127,255,cv.THRESH_TOZERO_INV)
 
titles = ['Original Image','BINARY','BINARY_INV','TRUNC','TOZERO','TOZERO_INV']
images = [img, thresh1, thresh2, thresh3, thresh4, thresh5]
 
#for i in range(6):
#    plt.subplot(2,3,i+1),plt.imshow(images[i],'gray',vmin=0,vmax=255)
#    plt.title(titles[i])
#    plt.xticks([]),plt.yticks([])
 
plt.subplot(1,1,1),plt.imshow(images[3],'gray',vmin=0,vmax=255)
plt.show()

#imagem = cv2.imread("img2.jpg")


#texto = pytesseract.image_to_string(imagem, config='--oem 3 --psm 6')

texto = pytesseract.image_to_string(images[3], config='--oem 3 --psm 6')

print("=========Resultado=========")
print(texto)

