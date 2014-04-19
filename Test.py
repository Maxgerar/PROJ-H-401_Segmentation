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
   
    # constructeur
    def __init__(self,fname):
        
        #image a charger
        self.name = fname
        
        #parametre de la segmentation
        self.segments = 0; # le nombre de superpixels dependra de la taille du morceau d'image auquel on s'interesse.
        self.compacite = 20.0 # pour avoir des pixels plus ou moins homog et de forme plus ou moins reguliere, on donne un tout petit peu plus d'importance au caract                #spatial
    
    def segmente(self):
        
        #lecture de l'image vers un ndarray. toutes les images fournies ont une taille de 12051000 pixels.
        im = imread(self.name)
        
        #Filtrage median pour enlever le bruit et eviter le repliement spectral en cas d'echantillonnage. Point positif : c'est un filtre qui conserve les bords !!!
        #plus le rayon du disque est important plus le lissage est fort et plus il y a risque de perte d'information, le filtre supprimant les details.
        im = rank.median(im,disk(8))
        
        #on reduit l'image pour diminuer le temps de computation. On s'interesse qu'a certaines parties de l'image plus echantillonnage. C'est l'image grayscale
        self.im_red = im[100:5000:2,300:3000:2]
        self.segments = (self.im_red.size)/550
        
        
        # slic attend une image rgb il faut donc faire la conversion
        self.img_temp= gray2rgb(self.im_red)
        
        # cette fonction attend egalement des valeurs d'intensite en float
        self.img = img_as_float(self.img_temp)
        
        #segmentation en superpixel, fonction slic de skimage.segmentation
        self.segments_slic = slic(self.img,n_segments = self.segments,compactness = self.compacite, sigma =1)
        
#        print self.segments_slic.shape
#        print find_boundaries(self.segments_slic).shape

        #on doit avoir tous les indices sup a 0 pour region props donc on les augmente tous de 1
        self.segments_slic = self.segments_slic + np.ones(self.segments_slic.shape,dtype = np.int64)
        
        
        # liste de proprietes par superpixel
        self.props = regionprops(self.segments_slic,intensity_image = self.im_red)
        
        #on creer une liste contenant tout les labels des superpixels
        self.regionlabels = list ()
        for elem in self.props:
            self.regionlabels.append(elem.label)
        

        #liste qui permettra de stocker les labels des superpixel qui ont ete colore
        self.colored_pixel_label = list()
        
        
        # Liaison de click avec la fonction onclick
        self.fig = plt.figure('segmentation')
        cid1 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        
        #Affichage
        self.affichage(mark_boundaries(self.img,self.segments_slic))
    
    
    #fonction a lancer si clic de souris
    def onclick(self,event):

        
        #identification du superpixel clicke
        superpixel = self.segments_slic[event.ydata,event.xdata]
        
        # si le pixel a deja ete colorie on le decolorie
        
        if self.props[superpixel-1].label in self.colored_pixel_label:
            # on le retire de la liste des pixel colorie
           self.colored_pixel_label.remove(self.props[superpixel-1].label)
           
           #on recupere les valeurs d'origine
           image = img_as_float(self.img_temp)
           
            #on decolorie le superpixel
           for row in self.props[superpixel-1].coords:
               self.img[row[0],row[1],0]=image[row[0],row[1],0]
               self.img[row[0],row[1],1]=image[row[0],row[1],1]
               self.img[row[0],row[1],2]=image[row[0],row[1],2]
    
        #sinon on le colorie lui et ses voisins
        else:
            
            #on colorie le pixel clique et on l'indique dans la liste
            self.color_superpixel(self.props[superpixel-1].coords)
            self.colored_pixel_label.append(self.props[superpixel-1].label)
            
            #fonction permettant de colorier les superpixels semblables appartenant a l'elem designe par l'utilisateur
            self.color_expand(superpixel-1)
        
            #fonction permettant d'etendre ca
            #pour tout les pixels du voisinage de celui qu'on a colorie on relance la mm fonction sur la liste de ces voisins
#            for elem in self.colored_temp:
#                self.color_expand(elem-1,self.regionlabels)
#            
#            #on remet a null la liste des voisins en attendant le prochain clik
#            self.colored_temp=[]

    
        #affichage des statistiques sur le superpixel clique
#        print median(self.props[superpixel-1].coords)
#        print std_dev(self.props[superpixel-1].coords)
#        print self.props[superpixel-1].label
#        print self.props[superpixel-1].mean_intensity
#        print self.mediane(self.props[superpixel-1].coords)
#        print self.std_dev(self.props[superpixel-1].coords)
#        print self.props[superpixel-1].centroid
    
        

        #en n'oubliant pas que la num de regioprops commence a zero alors que celle des superpixel commence a 1

        
        #on met a jour les changements
        self.obj.set_data(mark_boundaries(self.img,self.segments_slic))
        plt.draw()
    

    
    
    #fonction recursive qui va colorier l'elem designe par l'utilisateur et ses voisins qui lui sont suffisamment semblables
    def color_expand(self,indice):
        
        #param du superpixel dont on etudie le voisinage
        centre1 = self.props[indice].centroid
        mediane1 = self.mediane(self.props[indice].coords)

        #comparaison avec les autres superpixels de liste. liste est la liste des labels de superpixels concernes.
        for elem in self.regionlabels:
            
            if elem not in self.colored_pixel_label:

                #calcul de distance entre les centroides des superpixels
                centre2 = self.props[elem-1].centroid #le centre "mobile"
                distance = math.sqrt(((centre1[0]-centre2[0])**2)+((centre1[1]-centre2[1])**2))
            
                # Test pour savoir si les superpixels sont voisins
                if distance <=30:
               
               #maintenant on test la similarite en intensite via les mediane de distrib d'intensite des superpixels
               
                    mediane2 = self.mediane(self.props[elem-1].coords)
                    diff = math.fabs(mediane1-mediane2)
              
                    if diff <=12:
                        #on colorie le superpixel teste
                        self.color_superpixel(self.props[elem-1].coords)
                        #on indique dans une liste qu'on a colorie ce superpixel et on l'indique dans la liste des voisins
                        self.colored_pixel_label.append(elem)
                        #self.colored_temp.append(elem)
                        #recursivite
                        self.color_expand(elem-1)





    def affichage(self,image):
        #ligne pour reinitialiser
        self.obj = plt.imshow(image)
        plt.show()
    
    
    #fonction permettant de colorer un superpixel
    def color_superpixel(self,coords):
        for row in coords:
            self.img[row[0],row[1],0]=30
            self.img[row[0],row[1],1]=144
            self.img[row[0],row[1],2]=25

    #serie de fonctions pour effectuer des staistiques sur les superpixels

    def std_dev(self,coords):
        points = np.zeros(0)
        for row in coords:
            points= np.append(points,self.im_red[row[0],row[1]])
        return np.std(points)

#fonction permettant de calculer la mediane de la distribution d'intensite sur le superpixel
    def mediane(self,coords):
        points = np.zeros(0)
        for row in coords:
            points=np.append(points,self.im_red[row[0],row[1]])
        return np.median(points)




    #fonction qui va permettre de regrouper les superpixels en un plus petit nombre de clusters qui seront facilement coloriable
#def clustering(self):
    


        

        
        

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
    Im = ImgSegmentation('30.1.foto177a.12000x.TIF')
    Im.segmente()
    
