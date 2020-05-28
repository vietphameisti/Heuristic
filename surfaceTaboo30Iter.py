from scipy import *
from math import *
import matplotlib.pyplot as plt
from matplotlib import pyplot
from matplotlib.path import Path
import matplotlib.patches as patches
import pyclipper
from functools import *


# ***************** Paramètres du problème ******************
# Différentes propositions de parcelles :
#polygone = ((10,10),(10,400),(400,400),(400,10))
#polygone = ((10,10),(10,300),(250,300),(350,130),(200,10))
#polygone = ((50,150),(200,50),(350,150),(350,300),(250,300),(200,250),(150,350),(100,250),(100,200))
#polygone = ((50,50),(50,400),(220,310),(220,170),(330,170),(330,480),(450,480),(450,50))
def polygoneInput(i):
    switcher={
        1:((10,10),(10,400),(400,400),(400,10)),
        2:((10,10),(10,300),(250,300),(350,130),(200,10)),
        3:((50,150),(200,50),(350,150),(350,300),(250,300),(200,250),(150,350),(100,250),(100,200)),
        4:((50,50),(50,400),(220,310),(220,170),(330,170),(330,480),(450,480),(450,50))
    }
    return switcher.get(i)
#initialize  polygone input parameters
polygone=polygoneInput(4)

# Transforme le polygone en liste pour l'affichage.
def poly2list(polygone):
    polygonefig = list(polygone)
    polygonefig.append(polygonefig[0])
    return polygonefig

# Constante polygone dessinable
polygonefig = poly2list(polygone)

# to calcule the area of the surface and the area that we have found
def areasize(polygone):
    pola=list(polygone)
    p1=(pola[0],pola[1])
    p2=(pola[2],pola[3])
    return distance(p1[0],p1[1])*distance(p2[0],p2[1])

def lostarea(polygone,rect):
    return (areasize(polygone)-areasize(rect))

# Distance entre deux points (x1,y1), (x2,y2)
def distance(p1,p2):
    return sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

# Aire du rectangle (A(x1,y1), B(x2,y2), C(x3,y3), D(x4,y4))
# 	= distance AB * distance BC
def aire(rect):
    p1=rect[0]
    p2=rect[1]
    p3=rect[2]
    p4=rect[3]
    return (distance(p1,p2)*distance(p1,p4))


# Fenètre d'affichage
def dessine(polyfig,rectfig,canv):
#    global canv, codes
    global codes
    canv.clear()
    canv.set_xlim(0,500)
    canv.set_ylim(0,500)
    # Dessin du polygone
    codes = [Path.MOVETO]
    for i in range(len(polyfig)-2):
        codes.append(Path.LINETO)
    codes.append(Path.CLOSEPOLY)
    path = Path(polyfig, codes)
    patch = patches.PathPatch(path, facecolor='orange', lw=2)
    canv.add_patch(patch)

    # Dessin du rectangle
    codes = [Path.MOVETO]
    for i in range(len(rectfig)-2):
        codes.append(Path.LINETO)
    codes.append(Path.CLOSEPOLY)
    path = Path(rectfig, codes)
    patch = patches.PathPatch(path, facecolor='grey', lw=2)
    canv.add_patch(patch)

    # Affichage du titre (aire du rectangle)
    plt.title("Aire : {}".format(round(aire(rectfig[:-1]),2)))

    plt.draw()
    plt.pause(0.1)

# Récupère les bornes de la bounding box autour de la parcelle
def getBornes(polygone):
    lpoly = list(polygone) #tansformation en liste pour parcours avec reduce
    #return reduce(lambda (xmin,xmax,ymin,ymax),(xe,ye): (min(xe,xmin),max(xe,xmax),min(ye,ymin),max(ye,ymax)),lpoly[1:],(lpoly[0][0],lpoly[0][0],lpoly[0][1],lpoly[0][1]))
    return reduce(lambda acc,e: (min(e[0],acc[0]),max(e[0],acc[1]),min(e[1],acc[2]),max(e[1],acc[3])),lpoly[1:],(lpoly[0][0],lpoly[0][0],lpoly[0][1],lpoly[0][1]))
# Transformation d'une solution du pb (centre/coin/angle) en rectangle pour le clipping
# Retourne un rectangle (A(x1,y1), B(x2,y2), C(x3,y3), D(x4,y4))
def pos2rect(pos):
    # coin : point A
    xa, ya = pos[0], pos[1]
    # centre du rectangle : point O
    xo, yo = pos[2], pos[3]
    # angle  AÔD
    angle = pos[4]

    # point D : rotation de centre O, d'angle alpha
    alpha = pi * angle / 180 # degre en radian
    xd = cos(alpha)*(xa-xo) - sin(alpha)*(ya-yo) + xo
    yd = sin(alpha)*(xa-xo) + cos(alpha)*(ya-yo) + yo
    # point C : symétrique de A, de centre O
    xc, yc = 2*xo - xa, 2*yo - ya
    # point B : symétrique de D, de centre O
    xb, yb = 2*xo - xd, 2*yo - yd

    # round pour le clipping
    return ((round(xa),round(ya)),(round(xb),round(yb)),(round(xc),round(yc)),(round(xd),round(yd)))


# Clipping
# Prédicat qui vérifie que le rectangle est bien dans le polygone
# Teste si
# 	- il y a bien une intersection (!=[]) entre les figures et
#	- les deux listes ont la même taille et
# 	- tous les points du rectangle appartiennent au résultat du clipping
# Si erreur (~angle plat), retourne faux
def verifcontrainte(rect, polygone):
    try:
        # Config
        pc = pyclipper.Pyclipper()
        pc.AddPath(polygone, pyclipper.PT_SUBJECT, True)
        pc.AddPath(rect, pyclipper.PT_CLIP, True)
        # Clipping
        clip = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        #all(iterable) return True if all elements of the iterable are true (or if the iterable is empty)
        return (clip!=[]) and (len(clip[0])==len(rect)) and all(list(map(lambda e:list(e) in clip[0], rect)))
    except pyclipper.ClipperException:
        # print rect
        return False

# Crée un individu (centre/coin/angle) FAISABLE
# un individu est décrit par votre metaheuristique contenant au moins:
# 	- pos : solution (centre/coin/angle) liste des variables
#	- eval :  aire du rectangle
#	- ... : autres composantes de l'individu
def initUn(polygone):
    global xmin,xmax,ymin,ymax
    anglemin = 1
    anglemax = 89
    boolOK = False
    while not boolOK: # tant que non faisable
        xo=random.uniform(xmin,xmax)
        yo=random.uniform(ymin,ymax)
        xa=xo+pow(-1,random.randint(0,1))*random.uniform(10,min(xo-xmin,xmax-xo))
        ya=yo+pow(-1,random.randint(0,1))*random.uniform(10,min(yo-ymin,ymax-yo))
        angle = random.uniform(anglemin,anglemax)
        pos = [round(xa),round(ya),round(xo),round(yo),angle]
        rect = pos2rect(pos)
        # calcul du clipping
        boolOK = verifcontrainte(rect,polygone)
    ev = aire(pos2rect(pos))
    return {'pos':pos, 'eval':ev}


def generateNeighbor(polygone):
    #global xmin,xmax,ymin,ymax
    anglemin = 1
    anglemax = 89
    boolOK = False
    while not boolOK: # tant que non faisable
        xo=random.uniform(xmin,xmax)
        yo=random.uniform(ymin,ymax)
        xa=xo+pow(-1,random.randint(0,1))*random.uniform(10,min(xo-xmin,xmax-xo))
        ya=yo+pow(-1,random.randint(0,1))*random.uniform(10,min(yo-ymin,ymax-yo))
        angle = random.uniform(anglemin,anglemax)
        pos = [round(xa),round(ya),round(xo),round(yo),angle]
        rect = pos2rect(pos)
        # calcul du clipping
        boolOK = verifcontrainte(rect,polygone)
    ev = aire(pos2rect(pos))
    return {'pos':pos, 'eval':ev}

def bestNeighbor(path, nbNeigh, ltaboo):
    global bestV, bestDist
    #list of indices to swap to generate Neighbors
    b = generateNeighbor(polygone)
    bestV = b['pos']
    bestDist = b['eval']
    for i in range(nbNeigh):
        Neigh = generateNeighbor(polygone)
        if Neigh['pos'] not in ltaboo[:10]: #aspirion criteria
            d = Neigh['eval']
            if (d > bestDist):
                bestV = Neigh['pos']
                bestDist = d
    return (bestV,bestDist)

# *************************************** ALGO D'OPTIM ***********************************
# calcul des bornes pour l'initialisation
xmin,xmax,ymin,ymax = getBornes(polygone)
# initialisation de la population (de l'agent si recuit simulé) et du meilleur individu.
iterMax = 10000

def tabooSearch(nTabu,nNeigh):
    ntaboo = nTabu
    nbNeigh = nNeigh
    ltaboo = []       # taboo list
    boxplotData=[]

    #best=initUn(polygone)
    initsol = initUn(polygone) # choose randomly the first rectangle
    route = initsol['pos']
    dist = initsol['eval']
    best_route = route
    best_dist = dist
    i=0
# initialization of the taboo list
    ltaboo.insert(0,best_route)

    #display figure at each taboo list parameter
    # fig = plt.figure()
    # canv = fig.add_subplot(1,1,1)
    # canv.set_xlim(0,500)
    # canv.set_ylim(0,500)

# main loop of the taboo algorithm
    while i <= iterMax:
        # get the best Neighbor
        (Neighbor, dist) = bestNeighbor(route, nbNeigh, ltaboo)
        # comparison to the best, if it is better, save it and refresh the figure
        if dist > best_dist:
            best_dist = dist
            best_route = Neighbor
            #dessine(polygonefig, poly2list(pos2rect(best_route)),canv)
            boxplotData.append(dist)
        # add to taboo list
        ltaboo.insert(0,Neighbor)
        if (len(ltaboo) > ntaboo):
            ltaboo.pop()
        # next iteration
        i += 1
        route = Neighbor

    print("Size of the taboo list: ",ntaboo)
    # print("The Polygon's size:",areasize(polygone))
    print("Value of the rectangular that Tabu found",aire(poly2list(pos2rect(best_route))))
    # print("The variation between the Polygon and the area of rectangular",lostarea(polygone,poly2list(pos2rect(best_route))))
    #return boxplotData
    return boxplotData
# FIN : affichages
#dessine(polygonefig, poly2list(pos2rect(best_route)))
def boxplot(boxplotData=[]):
    print(boxplotData)
    fig=plt.figure()
    ax=fig.add_subplot()
    bp=ax.boxplot(boxplotData,patch_artist=True)
    pyplot.gca().xaxis.set_ticklabels(['TabuList size 1', 'TabuList size 50', 'TabuList size 100'])
    for box in bp['boxes']:
        # change outline color
        box.set( color='#7570b3', linewidth=2)
        # change fill color
        box.set( facecolor = '#1b9e77' )
    plt.show()
#nb=[1,50,100]
nb=[1,50,100]
boxplotData=[]
for i in nb:
    boxplotDataIter=[]
    for iter in range(30):
        boxplot=tabooSearch(i,30)
        boxplotDataIter.extend(boxplot)
    boxplotData.append(boxplotDataIter)

fig=plt.figure()
ax=fig.add_subplot()
bp=ax.boxplot(boxplotData,patch_artist=True)
pyplot.gca().xaxis.set_ticklabels(['TabuList size 1', 'TabuList size 50', 'TabuList size 100'])
for box in bp['boxes']:
    # change outline color
    box.set( color='#7570b3', linewidth=2)
    # change fill color
    box.set( facecolor = '#1b9e77' )
plt.show()

