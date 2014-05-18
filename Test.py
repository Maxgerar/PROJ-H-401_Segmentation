import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Button
import numpy as np
import math
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries,find_boundaries
from skimage.util import img_as_float
from skimage.io import imread
from skimage.color import gray2rgb
from skimage.measure import regionprops
from skimage.morphology import disk,remove_small_objects
from skimage.filter import rank
from skimage.filter import canny
from skimage.exposure import equalize_hist
import copy
from scipy.cluster.vq import whiten,kmeans2
import Tkinter


#interface utilisateur
#elle permet a l'utilisateur de fixer les paramtres de la segmentation, de choisir l'image sur laquelle travailler et de choisir un nom #pour l'enrgistrement du fichier
class Application (Tkinter.Tk):
    #constructeur de la fenetre graph
    def __init__(self):
        #appel du constructeur de la classe mere
        Tkinter.Tk.__init__(self)
        #initialisation des differents widgets de la fenetre
        self.grid()
        self.entrees()
        self.boutons()
        self.menu()
        self.grid_columnconfigure(0,weight=1)
            
    #champs de textes et labels
    def entrees(self):
        
        Tkinter.Label(self, text = "Nom").grid(row=0)
        Tkinter.Label(self,text = 'Nombre de superpixels').grid(row = 1)
        Tkinter.Label(self, text = "Compacite").grid(row=2)
        Tkinter.Label(self, text = "Choix de l'image").grid(row=4)
    
        self.name = Tkinter.StringVar(self)
        self.name.set("segmentation")
        self.nom = Tkinter.Entry(self,textvariable = self.name)
        self.nom.grid(column =1,row =0,sticky = 'E')

        self.compactness = Tkinter.StringVar(self)
        self.compactness.set("20.0")
        self.compact = Tkinter.Entry(self,textvariable = self.compactness)
        self.compact.grid(column =1,row=2,sticky = 'E')

        self.number = Tkinter.StringVar(self)
        self.number.set("5500")
        self.nombre = Tkinter.Entry(self,textvariable = self.number)
        self.nombre.grid(column = 1,row= 1, sticky = 'E')
    
        self.equalize = Tkinter.IntVar()
        self.check = Tkinter.Checkbutton(self,text = " egalisation d'histograme",variable = self.equalize)
        self.check.pack()
        self.check.grid(column = 1,row = 3, sticky = 'E')
    #boutons
    def boutons(self):
        self.button = Tkinter.Button(self,text = 'launch', command = self.onButtonClick)
        self.button.grid(column = 3, row = 5,sticky = 'W')
    
        self.extract = Tkinter.Button(self,text = 'extract',command = self.onButtonPressed)
        self.extract.grid(column = 3, row = 7, sticky = 'W')
    
        self.clustering =Tkinter.Button(self,text = 'clustering',command = self.onButtonDrop)
        self.clustering.grid(column = 3, row = 6, sticky = 'W')
    
    #menu deroulant
    def menu(self):
        self.options = ["1.2.foto1a.4000x.tiff","1.2.foto2a.12000x.tiff","1.2.foto3a.12000x.TIFF","1.2.foto4b.4000x.TIFF","1.2.foto5b.12000x.TIFF","2.1.foto11b.12000x.TIFF","1.2.foto6b.12000x.TIFF","2.1.foto7a.7000x.TIFF","2.1.foto8a.12000x.TIFF","2.1.foto9a.12000x.TIFF","2.1.foto10b.7000x.TIFF","4.1.foto19a.7000x.TIFF","30.1.foto180b.12000x.TIF","30.1.foto179b.12000x.TIF","30.1.foto177a.12000x.TIF","27.1.foto160b.4000x.TIFF","30.1.foto178b.4000x.TIF","3.1.foto14a.12000x.TIFF","3.1.foto15a.12000x.TIFF","3.1.foto16b.4000x.TIFF","3.1.foto17b.12000x.TIFF","3.1.foto18b.12000x.TIFF","5.1.foto25a.7000x.TIFF","5.1.foto27a.12000x.TIFF","7.1.foto38a.12000x.TIFF","8.1.foto44a.12000x.TIFF","9.1.foto53b.12000x.TIFF","11.1.foto65b.12000x.TIFF","13.1.foto77b.12000x.TIFF","14.1.foto81a.12000x.TIFF","16.1.foto92a.12000x.TIFF","17.1.foto101b.12000x.TIFF","19.1.foto114b.12000x.TIFF","21.1.foto125b.12000x.TIFF","23.1.foto135a.12000x.TIFF","25.1.foto148b.7000x.TIFF","26.1.foto152a.12000x.TIFF","26.1.foto153a.12000x.TIFF","27.1.foto161b.12000x.TIFF"]
        
        self.variable = Tkinter.StringVar(self)
        self.variable.set(self.options[0])#valeur par defaut
        
        self.file = apply(Tkinter.OptionMenu, (self,self.variable)+tuple(self.options))
        self.file.pack()
        self.file.grid(column =1,row = 4, sticky = 'E')
    
    # quand on a appuye sur launch, on lance l'image et la segmentation
    def onButtonClick(self):
        self.Im = ImgSegmentation(self.variable.get(),float(self.compactness.get()),int(self.number.get()),self.name.get(),self.equalize.get())
        self.Im.segmente()
    
    #methode a lancer quand on appui sur le bouton extract
    def onButtonPressed(self):
        self.Im.extract()

    #methode a lancer quand on appui sur le bouton clustering
    def onButtonDrop(self):
        self.Im.partitioning()









#classe realisant le traitement de l'image

class ImgSegmentation:
   
    # constructeur
    def __init__(self,fname,compactness,number,nomEnregistrement,egalisation):
        #image a charger
        self.name = fname
        #nom pour l'enregistrement du fichier
        self.enregistrement = nomEnregistrement
        #parametre de la segmentation
        self.segments = number
        self.compacite = compactness # on conseille la valeur par defaut de 20 pour avoir des pixels plus ou moins homog et de forme  #plus ou moins reguliere, on donne un tout petit peu plus d'importance au caract spatial
        #variable pour savoir si on fait l'egalisation d'hist
        self.equalizeHist = egalisation
    
    
    #la segmentation automatique de l'image
    def segmente(self):
        
        #lecture de l'image vers un ndarray. toutes les images fournies ont une taille de 12051000 pixels.
        self.im = imread(self.name)
        
        if self.equalizeHist == 1:
            self.im = equalize_hist(self.im)
        
        #Filtrage median pour enlever le bruit et eviter le repliement spectral en cas d'echantillonnage. Point positif : c'est un filtre qui conserve les bords !!!
        #plus le rayon du disque est important plus le lissage est fort et plus il y a risque de perte d'information, le filtre supprimant les details.
        self.im = rank.median(self.im,disk(8))
        
        #on reduit l'image pour diminuer le temps de computation. On ne s'interesse qu'a certaines parties de l'image plus echantillonnage. C'est l'image grayscale. On diminue par deux le nombre de pixels contenu dans l'image.
        self.im_red = self.im[::2,::2] #self.im[1000:2300:2,1500:3000:2] #self.im[::2,::2] # #

        
        # slic attend une image rgb il faut donc faire la conversion
        self.img_temp= gray2rgb(self.im_red)
        
        # cette fonction attend egalement des valeurs d'intensite en float
        self.img = img_as_float(self.img_temp)
        
        #segmentation en superpixel, fonction slic de skimage.segmentation, le parametre sigma prend la std dev d'un filtre gaussien applique a l'image avant de la segmenter
        self.segments_slic = slic(self.img,n_segments = self.segments,compactness = self.compacite, sigma =1)
        

        #on doit avoir tous les indices sup a 0 pour region props donc on les augmente tous de 1
        self.segments_slic = self.segments_slic + np.ones(self.segments_slic.shape,dtype = np.int64)
        
        # liste de proprietes par superpixel
        self.props = regionprops(self.segments_slic, intensity_image = self.im_red)
        
        # on cree la matrice d'adjacence
        self.create_neighbour_matrix()


        #liste qui permettra de stocker les labels des superpixel qui ont ete colore
        self.colored_pixel_label = list()


        # appliquons maintenant un deuxieme clustering sur ces superpixels base sur leurs proprietes
        #self.clustering()

        # Liaison de click avec la fonction onclick et des evenements clavier
        self.fig = plt.figure('segmentation')
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)


        #Affichage
        self.affichage(mark_boundaries(self.img,self.segments_slic))

#    def clustering(self):
#    
#        # essai clustering
#        #creation matrice d'observation chaque observation represente un superpixel
#        obs_matrix = np.zeros([len(self.props),3])
#        for elem in self.props:
#            obs_matrix[(elem.label)-1][0] = 100000*elem.centroid[0]
#            obs_matrix[(elem.label)-1][1] = 100000*elem.centroid[1]
#            obs_matrix[(elem.label)-1][2] = self.mediane(elem.coords)
#    
#    
#    
#        #on whiten la matrice avant de lancer le k-means
#        whitened = whiten(obs_matrix)
#    
#        #appliquons le kmeans
#        self.result = kmeans2(whitened,len(self.props)/30,1000,minit='points')
#    
#        #result[1] contient le label du cluster auquel chaque obs (=superpixel) appatient
#        self.clusters = self.result[1]

        
        
        #fonction a lancer si clic de souris, segmentation reposant sur l'utilisateur
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
#            #identification des superpixels appartenant a celui-ci et coloriage des superpixels en question si assez proches du superpixel clicke
#            for indice in range(len(self.clusters)):
#                #centre = self.props[indice].centroid
#                #distance = math.sqrt(((centre_click[0]-centre[0])**2)+((centre_click[1]-centre[1])**2))
#                if self.clusters[indice]==megapixel: #and distance <= 40:
#                   self.color_superpixel(indice)
#                   self.colored_pixel_label.append(self.props[indice].label)
#                   #self.color_expand(indice,self.mediane(self.props[indice].coords))

            
            
            #sinon on le colorie lui et ses voisins
        else:
                
            #on colorie le pixel clique et on l'indique dans la liste
            self.color_superpixel(superpixel-1)
            self.colored_pixel_label.append(self.props[superpixel-1].label)
                
            #            #fonction permettant de colorier les superpixels semblables appartenant a l'elem designe par l'utilisateur
            self.color_expand(superpixel-1,self.mediane(self.props[superpixel-1].coords))

            
            
        #on met a jour les changements
        self.obj.set_data(mark_boundaries(self.img,self.segments_slic))
        plt.draw()
        
        
        
        # fonction recursive qui colorie le voisins du superpixel "indice" qui lui sont semblables
    def color_expand(self,indice,median):
        #param du superpixel dont on etudie le voisinage
        mediane1 = median
        # on cherche dans ces voisins
        for column in range(len(self.props)):
            # si c'est un voisin et qu'il n'a pas encore ete colorie
            if self.neighbourhood_matrix[indice,column]==1 and (column+1) not in self.colored_pixel_label:
                
                #on test la similarite en intensite via les mediane de distrib d'intensite des superpixels
                
                mediane2 = self.mediane(self.props[column].coords)
                diff = math.fabs(mediane1-mediane2)
                
                if diff <=12:
                    #on colorie le superpixel teste
                    self.color_superpixel(column)
                    #on indique dans une liste qu'on a colorie ce superpixel
                    self.colored_pixel_label.append(column+1)
                    
                    #recursivite
                    mediane1 = (mediane1+mediane2)/2
                    self.color_expand(column,mediane1)
        



    #cette fonction cree une matrice d'ajancement. cette matrice est de taille NxN ou N est le nombre de superpixels, elle indique pour chaque superpixel les superpixels qui lui sont adjacents par un "1" dans  l'elem de la matrice en question. Ainsi si les superpixel 1 et 2 sont voisins, il y aura un "1" en Matrice[1,2] et en Matrice de [2,1]
    
    def create_neighbour_matrix(self):
        bounds = find_boundaries(self.segments_slic)
        N = len(self.props)
        #matrice d'adjacence
        self.neighbourhood_matrix = np.zeros((N,N))
        #on parcourt les pixels pour savoir s'ils font partie d'une frontiere
        for row in range(bounds.shape[0]):
            for column in range(bounds.shape[1]):
                #si le pixel appartient a un frontiere, on check le label de ces voisins
                if bounds[row,column]==1:
                    if row != 0 and row != (bounds.shape[0]-1) and column != 0 and column != (bounds.shape[1]-1):
                        if self.segments_slic[row-1,column] != self.segments_slic[row+1,column]:
                            self.neighbourhood_matrix[self.segments_slic[row-1,column]-1,self.segments_slic[row+1,column]-1]=1
                            self.neighbourhood_matrix[self.segments_slic[row+1,column]-1,self.segments_slic[row-1,column]-1]=1
                        if self.segments_slic[row,column-1] != self.segments_slic[row,column+1]:
                            self.neighbourhood_matrix[self.segments_slic[row,column-1]-1,self.segments_slic[row,column+1]-1]=1
                            self.neighbourhood_matrix[self.segments_slic[row,column+1]-1,self.segments_slic[row,column-1]-1]=1
                #attention si on est sur un bord
                    elif row ==0 or row == bounds.shape[0]-1:
                            if self.segments_slic[row,column-1] != self.segments_slic[row,column+1]:
                                self.neighbourhood_matrix[self.segments_slic[row,column-1]-1,self.segments_slic[row,column+1]-1]=1
                                self.neighbourhood_matrix[self.segments_slic[row,column+1]-1,self.segments_slic[row,column-1]-1]=1

                    elif column == 0 or column == bounds.shape[1]-1:
                            if self.segments_slic[row-1,column] != self.segments_slic[row+1,column]:
                                self.neighbourhood_matrix[self.segments_slic[row-1,column]-1,self.segments_slic[row+1,column]-1]=1
                                self.neighbourhood_matrix[self.segments_slic[row+1,column]-1,self.segments_slic[row-1,column]-1]=1






    def partitioning(self):
        self.clean_colored_pixel()
        self.superpixel_dbscan(12)
        
        #figure pour montrer l'effet du clustering
        self.fig_cluster = plt.figure('segmentation et clustering')
        #on y lie la fonction qui permet de faire le coloriage
        self.cid2 = self.fig_cluster.canvas.mpl_connect('button_press_event', self.onmouseclicked)
        
        self.affichage(mark_boundaries(self.img,self.clusterized))

    def clean_colored_pixel(self):
        self.img = img_as_float(self.img_temp)
        for elem in self.colored_pixel_label:
#            #on decolorie l'elem
#            for row in self.props[elem-1].coords:
#                self.img[row[0],row[1],0]=image[row[0],row[1],0]
#                self.img[row[0],row[1],1]=image[row[0],row[1],1]
#                self.img[row[0],row[1],2]=image[row[0],row[1],2]
#            # et on le retire de la liste
            self.colored_pixel_label.remove(self.props[elem-1].label)



    # fonction realisant le partionnement dbscan sur les superpixels
    def superpixel_dbscan(self,eps):
    
    # nombre de superpixels
        Np = len(self.props)
    # vecteur qui reprendra pour chaque superpixel de l'image segmentee, le numero du cluster auquel il appartient
        self.regionsC = np.zeros(Np)
    # compteur du nombre de clusters
        Nc = 0
    # liste contenant pour chaque cluster la liste des indices des superpixels le formant
        self.C = list()
    #liste pour garder une trace des superpixel qui ont deja ete rencontre
        self.visited_superpixel_list = list()
    
    #on passe en revue les superpixels non encore visite,indice donne label-1 du superpixel
        for indice in range(Np):
            #si le superpixel d'indice Np+1 n'a pas encore ete visite
            if (indice+1) not in self.visited_superpixel_list:
                #on le marque comme visite
                self.visited_superpixel_list.append(indice+1)
                #on trouve ses voisins
                self.neighbours_list = self.find_neighbours_eps(indice,eps)
                #on forme un nouveau cluster
                Nc = Nc+1
                #on indique a quel cluster le superpixel appartient dans regionsC
                self.regionsC[indice] = Nc
                #on indique le label de ce superpixel dans la liste C, indiquant ainsi le superpixel indice comme appartennt au cluster Nc
                self.C.append(indice+1)
                #on parcourt maintenant son voisinage
                for elem in self.neighbours_list:
                    # si le voisin n'a pas encore ete visite
                    if elem not in self.visited_superpixel_list:
                    #on l'ajoute a la liste des superpixels visite
                       self.visited_superpixel_list.append(elem)
                    #on chercher ces propres voisins
                       self.sub_neighbours_list = self.find_neighbours_eps(elem-1,eps)
                    # et on l'ajoute a la liste de base des voisins
                       self.neighbours_list.extend(self.sub_neighbours_list)
                # si l'elem considere n'est pas encore dans un cluster, on l'ajoute au cluster courant
                # si sa valeur de regionC est nulle c'est que le superpixel n'appartient pas encore a un cluster
                    if self.regionsC[elem-1]==0:
                        #on l'ajoute au cluster courant
                        self.regionsC[elem-1]=Nc
                        # on ajoute son indice dans la liste des indices du cluster Nc
                        self.C[Nc-1] = [self.C[Nc-1],elem]
    
    #on genere maintenant la nouvelle image labellise
        self.clusterized = np.zeros(self.segments_slic.shape)
        #on parcourt la liste et on la rempli avec la numero du cluster auquel appartient le superpixel qui etait la avant
        for row in range(self.segments_slic.shape[0]):
            for column in range(self.segments_slic.shape[1]):
                self.clusterized[row,column] = self.regionsC[self.segments_slic[row,column]-1]



    #permet de trouver les voisins au sens de eps du superpixel d'indice ind_superpixel et renvoie cette liste
    def find_neighbours_eps(self,ind_superpixel,eps):
        list_of_neighbours = list()
        mediane1 = self.mediane(self.props[ind_superpixel].coords)
    #on parcout le ligne correspondant au superpixel dans la matrice d'adjacence
        for column in range(len(self.props)):
            if self.neighbourhood_matrix[ind_superpixel,column]==1 and (column+1) not in self.visited_superpixel_list :
               mediane2 = self.mediane(self.props[column].coords)
               diff = math.fabs(mediane1-mediane2)
               if diff <=eps:
                  list_of_neighbours.append(column+1)
        return list_of_neighbours
    
    
    # fonction a lancer suite a un clique de souris dans la fenetre du clustering dbscan
    def onmouseclicked(self,event):
        #identification du cluster pointe par l'utilisateur
        n_cluster = self.clusterized[event.ydata,event.xdata]
        #recuperation des indices de superpixels formant ce cluster
        for i in range (len(self.regionsC)):
            if self.regionsC[i]==n_cluster:
               self.color_superpixel(i)
               self.colored_pixel_label.append(i+1)
        
        #mise a jour des changement
        self.obj.set_data(mark_boundaries(self.img,self.clusterized))
        plt.draw()

    # fonction permettant d'afficher l'element d'interet seul dans une nouvelle figure
    def extract(self):

        if len(self.colored_pixel_label)==0:
            print " vous n'avez rien selectionne"

        else:
    
        #on creer une matrice vide de la taille de notre image cette taille c'est self.im_red.size
            self.im_extraction = np.ones(self.img.shape)
            image = img_as_float(self.img_temp)
            for elem in self.colored_pixel_label:
                coords = self.props[elem-1].coords
                for row in coords:
                    self.im_extraction[row[0],row[1],0]=image[row[0],row[1],0]
                    self.im_extraction[row[0],row[1],1]=image[row[0],row[1],1]
                    self.im_extraction[row[0],row[1],2]=image[row[0],row[1],2]
    
            self.figfinal = plt.figure('objet extrait :'+ self.enregistrement)
            self.affichage(self.im_extraction)


# fonctions " utilitaires"

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





if __name__ == "__main__":

    app = Application()
    app.title('outil de segmentation')
    app.mainloop()


