import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Button
import numpy as np
import math
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries, find_boundaries
from skimage.util import img_as_float
from skimage.io import imread
from skimage.color import gray2rgb
from skimage.measure import regionprops
from skimage.morphology import disk
from skimage.filter import rank
from skimage.filter import canny
import copy


class ImgSegmentation:
   
    
    def __init__(self,fname):
        self.name = fname
        self.segments = 1000; # segmentation assez fine
        self.compacite = 20.0 # pour avoir des pixels plus ou moins homog, on donne autant de poids a la couleur qu'au caract spatial
    
    #fonction a lancer si clic de souris
    def onclick(self,event):

        
        #on veut changer la couleur du superpixel sur lequel on vient de cliquer
        
        #identification du superpixel
        
        superpixel = self.segments_slic[event.ydata,event.xdata]
        pix_liste = copy.deepcopy(self.props)
        print pix_liste[0].label
        #self.color(superpixel-1,pix_liste)
        
        
#        print self.props[superpixel-1].mean_intensity
#        print self.props[superpixel-1].label
#        print self.props[superpixel-1].centroid
        
        
        #coloriage d'un superpixel
        #ensuite, grace a region props, on trouve l'ensembre des pixels formant ce superpixel
        #en n'oubliant pas que le num de regioprops commence a zero alors que celle des superpixel commence a 1
#        for row in self.props[superpixel-1].coords:
#            self.img[row[0],row[1],0]=30
#            self.img[row[0],row[1],1]=144
#            self.img[row[0],row[1],2]=255
        
        
        
        #on met a jour les changements
        self.obj.set_data(mark_boundaries(self.img,self.segments_slic))
        plt.draw()
    
    
    #fonction recursive qui va colorier l'elem designe par l'utilisateur
    def color(self,indice,liste):
        
        #param du superpixel choisi par l'utilisateur
        centre1 = self.props[indice].centroid
        mean1 = self.props[indice].mean_intensity
        
        
        for elem in liste:
            #calcul de distance entre les centroides des superpixels
            centre2 = elem.centroid #le centre "mobile"
            distance = math.sqrt(((centre1[0]-centre2[0])**2)+((centre1[1]-centre2[1])**2))
            
            # Test pour savoir si les superpixels sont voisins
            if distance <=30:
               
            #maintenant on test la similarite en intensite
               
               mean2 = elem.mean_intensity
               mean = math.fabs(mean1-mean2)
              
               if mean <=15:
            #on colorie le superpixel teste
                  for row in elem.coords:
                      self.img[row[0],row[1],0]=30
                      self.img[row[0],row[1],1]=144
                      self.img[row[0],row[1],2]=255
                    


#                #on recupere l'indice du superpixel dans le liste
#                  index = (elem.label)-1
#                #on retire le superpixel colorie de la liste
#                  liste_red = copy.deepcopy(liste)
#                  liste_red = liste_red.pop(liste.index(elem))
#                #on rapelle la methode sur la liste
#                  self.color(index,liste_red)




    def segmente(self):
    
        #lecture de l'image vers un ndarray
        im = imread(self.name)
        
        #on filtre pour enlever le bruit et avant d'echantillonner pour eviter l'aliasing
        #plus le rayon du disque est important plus le lissage est efficace
        #im = rank.median(im,disk(8))
        
        #on reduit l'image pour diminuer le temps de computation. On s'interesse qu'a certaines parties de l'image plus echantillonnage. C'est l'image grayscale
        self.im_red = im[600:2300:2,1100:3000:2]
        
        # slic attend une image rgb il faut donc faire la conversion
        img_temp = gray2rgb(self.im_red)
        self.img = img_as_float(img_temp)

        #segmentation en superpixel
        self.segments_slic = slic(self.img,n_segments = self.segments,compactness = self.compacite, sigma =1)
        
        #on doit avoir tous les indices sup a 0 pour region props donc on les augmente tous de 1
        self.segments_slic = self.segments_slic + np.ones(self.segments_slic.shape,dtype = np.int64)
        
        
        # liste de proprietes par superpixel
        self.props = regionprops(self.segments_slic,intensity_image = self.im_red)
        print type(self.props[0])

            
        #Test mettre tout le pixel "1" en bleu
#        for row in self.props[2].coords:
#            self.img[row[0],row[1],0]=30
#            self.img[row[0],row[1],1]=144
#            self.img[row[0],row[1],2]=255
            #probleme dans la segmentation des superpixels apparamment differents porte le mm label. Demander a Mr debeir
        
        #Test pour enlever les superpixel trop petits
        #voir avec regionprops dans measure de skimage donne les diff area et coord-> elimniation facile !
#        for i in range(len(props)):
#            if props[i].area <2000:
#            #il faut trouver comment supprimer des superpixels trop petits-> les inclure dans les plus gros mais comment savoir lequel
#               for row in props[i].coords:
#                   segments_slic[row[0],row[1]] = -1


            
        # Liaison de click avec la fonction onclick
        self.fig = plt.figure('segmentation')
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
                
        #Affichage
        self.affichage(mark_boundaries(self.img,self.segments_slic))

    def affichage(self,image):
        #ligne pour reinitialiser
        self.obj = plt.imshow(image)
        plt.show()

#    def original(self):
#        #lecture de l'image vers un ndarray
#        im = imread(self.name)
#        
#        self.fig,ax = plt.subplots()
#        self.obj = plt.imshow(im,cmap =cm.gray)
#
#        axes = plt.axes([0.7, 0, 0.1, 0.055])
#        button = Button(axes, 'Segmente')
#        button.on_clicked(self.reaction)
#        plt.show()
#        
#
#    def reaction(self,event):
#        self.segmente()
#        

        







if __name__ == "__main__":
    Im = ImgSegmentation('1.2.foto1a.4000x.tiff')
    Im.segmente()
    
