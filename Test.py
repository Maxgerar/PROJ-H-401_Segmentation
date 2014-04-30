import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Button
import numpy as np
import math
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
from skimage.io import imread
from skimage.color import gray2rgb
from skimage.measure import regionprops
from skimage.morphology import disk
from skimage.filter import rank
from skimage.filter import canny
from skimage.exposure import equalize_hist
import copy
from scipy.cluster.vq import whiten,kmeans2
import Tkinter

class Application (Tkinter.Tk):
    #constructeur de la fenetre graph
    def __init__(self):
        Tkinter.Tk.__init__(self)
        #self.parent = parent
        self.initialize()
    
    #permet d'initialiser tous les widgets de l'appli
    def initialize(self):
        self.grid()
        self.entrees()
        self.bouton()
        self.menu()
        self.grid_columnconfigure(0,weight=1)

    def entrees(self):
        
        Tkinter.Label(self, text = "Nom").grid(row=0)
        Tkinter.Label(self,text = 'Nombre de superpixel').grid(row = 1)
        Tkinter.Label(self, text = "Compacite").grid(row=2)
        Tkinter.Label(self, text = "Choix de l'image").grid(row=3)
    

        self.nom = Tkinter.Entry(self)
        self.nom.grid(column =1,row =0,sticky = 'E')

        self.compact = Tkinter.Entry(self)
        self.compact.grid(column =1,row=2,sticky = 'E')

        self.nombre = Tkinter.Entry(self)
        self.nombre.grid(column = 1,row= 1, sticky = 'E')

    def bouton(self):
        self.button = Tkinter.Button(self,text = 'launch')
        self.button.grid(column = 2, row = 4,sticky = 'W')

    def menu(self):
        self.options = ["1.2.foto1a.4000x.tiff","1.2.foto2a.12000x.tiff","1.2.foto3a.12000x.TIFF","1.2.foto4b.4000x.TIFF","1.2.foto5b.12000x.TIFF","2.1.foto11b.12000x.TIFF","1.2.foto6b.12000x.TIFF","2.1.foto7a.7000x.TIFF","2.1.foto8a.12000x.TIFF","2.1.foto9a.12000x.TIFF","2.1.foto10b.7000x.TIFF","4.1.foto19a.7000x.TIFF","30.1.foto180b.12000x.TIF","30.1.foto179b.12000x.TIF","30.1.foto177a.12000x.TIF","27.1.foto160b.4000x.TIFF","30.1.foto178b.4000x.TIF"]
        
        variable = StringVar(self)
        variable.set(options[0])#valeur par defaut
        
        self.file = self.apply(OptionMenu, (self,variable)+tuple(options))
        self.file.pack()
        self.file.grid(column =1,row = 3, sticky = 'E')




class ImgSegmentation:
   
    # constructeur
    def __init__(self,fname):
        
        #image a charger
        self.name = fname
        
        #parametre de la segmentation
        #self.segments = 0; # le nombre de superpixels dependra de la taille du morceau d'image auquel on s'interesse.
        self.compacite = 20.0 # pour avoir des pixels plus ou moins homog et de forme plus ou moins reguliere, on donne un tout petit peu plus d'importance au caract                #spatial
    
    def segmente(self):
        
        #lecture de l'image vers un ndarray. toutes les images fournies ont une taille de 12051000 pixels.
        im = imread(self.name)
        im = equalize_hist(im)
        #Filtrage median pour enlever le bruit et eviter le repliement spectral en cas d'echantillonnage. Point positif : c'est un filtre qui conserve les bords !!!
        #plus le rayon du disque est important plus le lissage est fort et plus il y a risque de perte d'information, le filtre supprimant les details.
        im = rank.median(im,disk(8))
        
        #on reduit l'image pour diminuer le temps de computation. On s'interesse qu'a certaines parties de l'image plus echantillonnage. C'est l'image grayscale
        self.im_red =  im[600:2300:2,1100:3000:2] #im[::2,::2]
        #detremination du nombre approximatif de superpixels
        self.segments = (self.im_red.size)/550
        
        
        # slic attend une image rgb il faut donc faire la conversion
        self.img_temp= gray2rgb(self.im_red)
        
        # cette fonction attend egalement des valeurs d'intensite en float
        self.img = img_as_float(self.img_temp)
        
        #segmentation en superpixel, fonction slic de skimage.segmentation
        self.segments_slic = slic(self.img,n_segments = self.segments,compactness = self.compacite, sigma =1)
        

        #on doit avoir tous les indices sup a 0 pour region props donc on les augmente tous de 1
        self.segments_slic = self.segments_slic + np.ones(self.segments_slic.shape,dtype = np.int64)
        
        
        # liste de proprietes par superpixel img_temp ou img_red ?
        self.props = regionprops(self.segments_slic,intensity_image = self.im_red)
        
        
        #on creer une liste contenant tout les labels des superpixels
        self.regionlabels = list ()
        for elem in self.props:
            self.regionlabels.append(elem.label)
       

        #liste qui permettra de stocker les labels des superpixel qui ont ete colore
        self.colored_pixel_label = list()

#        #narray pour le k centre initiaux
#        self.initial_centers = np.zeros([20,3])
#        #nombre
#        self.iter = 0

        # appliquons maintenant un deuxieme clustering sur ces superpixels base sur leurs proprietes
        #self.clustering()

        # Liaison de click avec la fonction onclick et des evenements clavier
        self.fig = plt.figure('segmentation')
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        #self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.onmouseclicked)
        #cid2 = self.fig.canvas.mpl_connect('key_press_event', self.on_key)




        #Affichage
        self.affichage(mark_boundaries(self.img,self.segments_slic))
            
            
#    # focntion a enclencher au debut pour choisir les centre initiaux du clustering
#    def onmouseclicked(self,event):
#        
#        if self.iter <20 :
#            print "centre"
#            #identification du superpixel clique
#            superpixel = self.segments_slic[event.ydata,event.xdata]
#    
#            # ajout du vecteur d'observation correspondant a ce superpixel a la liste des centre initiaux
##            temp = [100*self.props[superpixel-1].centroid[0],100*self.props[superpixel-1].centroid[1],self.props[superpixel-1].mean_intensity,self.mediane(self.props[superpixel-1].coords),self.std_dev(self.props[superpixel-1].coords)]
#
#            self.initial_centers[self.iter] = [100000*self.props[superpixel-1].centroid[0],100000*self.props[superpixel-1].centroid[1],self.mediane(self.props[superpixel-1].coords)]
#            self.iter = self.iter +1
#            
#            
#        else :
#            # il est temps pour le clustering
#            print self.initial_centers
#            print "bien"
#            self.clustering()
#            #changement de la fonction liee au click de souris
#            #on deconnecte le fenetre de la premier fonction "mouseclicked"
#            self.fig.canvas.mpl_disconnect(self.cid1)
#            #on la connecte mtn a onclick qui permet le coloriage
#            self.cid3 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
#            print "ok"

    
#    # fonction a lancer une fois qu'on a selectionne les centre initiaux pour lancer le clustering
#    def on_key(self,event):
#        print "bien"
##        self.clustering()
##        
##        # changement de la fonction liee au click de souris
##        #on deconnecte le fenetre de la premier fonction "mouseclicked"
##        self.fig.canvas.mpl_disconnect(cid1)
##        #on la connecte mtn a onclick qui permet le coloriage
##        cid3 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
##        print "ok"


    
    
    
    def clustering(self):
        
        # essai clustering
        #creation matrice d'observation chaque observation represente un superpixel
        obs_matrix = np.zeros([len(self.props),3])
        for elem in self.props:
            obs_matrix[(elem.label)-1][0] = 100000*elem.centroid[0]
            obs_matrix[(elem.label)-1][1] = 100000*elem.centroid[1]
            #obs_matrix[(elem.label)-1][2] = elem.mean_intensity
            obs_matrix[(elem.label)-1][2] = self.mediane(elem.coords)
            #obs_matrix[(elem.label)-1][4] = self.std_dev(elem.coords)
        
        
        #on whiten la matrice avant de lancer le k-means
        whitened = whiten(obs_matrix)
        
        #appliquons le kmeans
        self.result = kmeans2(whitened,len(self.props)/30,1000,minit='points')
#        #essai avec le choix des centre initiaux
#        self.result = kmeans2(whitened,self.initial_centers,100)

        #result[1] contient le label du cluster auquel chaque obs (=superpixel) appatient
        self.clusters = self.result[1]
     
    
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
#        else:
#            #identification du megapixel auquel il appartient
#            megapixel = self.clusters[superpixel-1]
#        
#            #identification des superpixels appartenant a celui-ci et coloriage des superpixels en question
#            for indice in range(len(self.clusters)):
#                if self.clusters[indice]==megapixel:
#                   self.color_superpixel(indice)
#                   self.colored_pixel_label.append(self.props[indice].label)


        #sinon on le colorie lui et ses voisins
        else:
            
            #on colorie le pixel clique et on l'indique dans la liste
            self.color_superpixel(superpixel-1)
            self.colored_pixel_label.append(self.props[superpixel-1].label)
            
#            #fonction permettant de colorier les superpixels semblables appartenant a l'elem designe par l'utilisateur

#            #self.color_expand(self.props[superpixel-1].centroid,self.mediane(self.props[superpixel-1].coords))
            self.color_expand(superpixel-1,self.mediane(self.props[superpixel-1].coords))


    
        #on met a jour les changements
        self.obj.set_data(mark_boundaries(self.img,self.segments_slic))
        plt.draw()
    



    #fonction recursive qui va colorier l'elem designe par l'utilisateur et ses voisins qui lui sont suffisamment semblables
    def color_expand(self,indice,median):
    
        #param du superpixel dont on etudie le voisinage
        mediane1 = median
        centre1 = self.props[indice].centroid
        #mediane1 = self.mediane(self.props[indice].coords)
    
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
                        self.color_superpixel(elem-1)
                        #on indique dans une liste qu'on a colorie ce superpixel
                        self.colored_pixel_label.append(elem)

                        #recursivite
                        mediane1 = (mediane1+mediane2)/2
                        self.color_expand(elem-1,mediane1)





    def affichage(self,image):
        #ligne pour reinitialiser
        self.obj = plt.imshow(image)
        plt.show()
    

    
    
    #fonction permettant de colorer un superpixel
    def color_superpixel(self,superpixel):
        coords = self.props[superpixel].coords
        for row in coords:
            self.img[row[0],row[1],0]=30
            self.img[row[0],row[1],1]=144
            self.img[row[0],row[1],2]=25

    #serie de fonctions pour effectuer des staistiques sur les superpixels
    #fonction calculant l'ecart type de la distrib d'intensite sur le superpixel
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

#    app = Application()
#    app.title('outil de segmentation')
#    app.mainloop()
    Im = ImgSegmentation('1.2.foto1a.4000x.tiff')
    Im.segmente()

