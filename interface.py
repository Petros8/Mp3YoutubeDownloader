from tkinter import *
import tkinter.messagebox
import tkinter.filedialog
import threading
import json
import urllib.request
import youtube_dl
import configparser
import pickle

# Support Classes

class Video:

	def __init__(self,id,title):
		self.id = id
		self.title = title

	def __str__(self):
		return self.title

class GoogleApiHandler(threading.Thread):

	def __init__(self,link):
		threading.Thread.__init__(self)
		self.link = link
		self.apikey = "AIzaSyDnbemBEO94pqWSF00fsprUejEvrV-kXiw"

	def idSeparator(self,link,isplaylist=False):
		if isplaylist:
			(url,playlistid) = link.split("list=")
			print("URL     :"+url)
			print("PLAYLIST ID    :"+playlistid)
			return playlistid
		else:
			(url,atrs) = link.split("v=")
			if "&" in atrs:
				(videoid,otheratrs) = atrs.split("&",1)
			else:
				videoid = atrs
			return videoid

	def run(self):
		videosList = self.getInfo()
		for item in videosList:
			listToDownload.append(item)
			videoList.insert(END,item)

			writeListFile()

		activeApiThread = GoogleApiHandler(link.get())
		link.set("")
		status.set("Pronto.")

	def getDataVideo(self,videoid):
		listaDeRetorno = []
		url = "https://www.googleapis.com/youtube/v3/videos?id="+videoid+"&key="+self.apikey+"&part=snippet"
		data = urllib.request.urlopen(url)

		lista = json.loads(data.readall().decode("utf-8"))
			
		for item in lista["items"]:
			listaDeRetorno.append(Video(videoid,item["snippet"]["title"]))
		return listaDeRetorno

	def getDataPlaylist(self,playlistid):
		
		listaDeRetorno = []
		lista = {"nextPageToken": ""}
		
		while "nextPageToken" in lista:
			
			url = "https://www.googleapis.com/youtube/v3/playlistItems?playlistId="+playlistid+"&key="+self.apikey+"&part=snippet,contentDetails&maxResults=50&pageToken="+lista["nextPageToken"]
	
			data = urllib.request.urlopen(url)

			lista = json.loads(data.readall().decode("utf-8"))

			for item in lista["items"]:
				listaDeRetorno.append(Video(item["contentDetails"]["videoId"],item["snippet"]["title"]))

		return listaDeRetorno
	
	def getInfo(self):

		returnLista = []

		if "watch?" in self.link and "list=" in self.link:
			
			answer = tkinter.messagebox.askquestion("Aviso","O seu link possui o dois atributos, uma playlist e um vídeo, deseja usar a playlist?")
			
			if answer == "yes":
				playlistid = self.idSeparator(self.link,True)
				returnLista = self.getDataPlaylist(playlistid)
			else:
				videoid = self.idSeparator(self.link)
				returnLista = self.getDataVideo(videoid)


		elif "watch?" in self.link:
			videoid = self.idSeparator(self.link)
			returnLista = self.getDataVideo(videoid)
			
		
		elif "list=" in self.link:
			playlistid = self.idSeparator(self.link,True)
			returnLista = self.getDataPlaylist(playlistid)
		
		else:
			tkinter.messagebox.showinfo("Alerta","Link inválido")
		return returnLista

class musicDownloader(threading.Thread):
	  
	def __init__(self,listToDownload,destiny):
	 	threading.Thread.__init__(self)
	 	self.listToDownload = listToDownload
	 	self.destiny = destiny
    
	def stop(self):
		self._stop.set()


	def run(self): 	
		
		global stopDownloadFlag
		copyList = list(self.listToDownload)

		for item in copyList:
			try:
				status.set("Baixando musica: "+ item.title)
				ydl_opts = {
    			'format': 'bestaudio/best',
    			'outtmpl': self.destiny+'/'+item.title+".%(ext)s",
    			'postprocessors': [{
        		'key': 'FFmpegExtractAudio',
        		'preferredcodec': 'mp3',
        		'preferredquality': '192',

    			}],
	
				}
		
				try:
					with youtube_dl.YoutubeDL(ydl_opts) as ydl:
						ydl.download(['http://www.youtube.com/watch?v='+item.id])
						videoList.delete(0)
						listToDownload.remove(item)
						writeListFile()
						if stopDownloadFlag == True:
							
							activeDownloaderThread = musicDownloader(listToDownload,link.get())
							stopDownloadFlag = False
							break

				except youtube_dl.utils.DownloadError:
					pass
			except:
				pass
		status.set("Pronto.")

# Configuração do main Frame

root = Tk()
root.resizable(width=False, height=False)
root.title("Mp3 Youtube Downloader - By Petros")
w = 804 # width for the Tk root
h = 605 # height for the Tk root

# get screen width and height
ws = root.winfo_screenwidth() # width of the screen
hs = root.winfo_screenheight() # height of the screen

# calculate x and y coordinates for the Tk root window
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# set the dimensions of the screen 
# and where it is placed
root.geometry('%dx%d+%d+%d' % (w, h, x, y))

# Variáveis
destiny = StringVar()
link = StringVar()
status = StringVar(root,"Pronto.")
listToDownload = []
activeApiThread = GoogleApiHandler(link.get())
activeDownloaderThread = musicDownloader(listToDownload,link.get())
stopDownloadFlag = False

configFile = configparser.ConfigParser()

configFile.read("config.ini")

if "Directory" in configFile:
	destiny.set(configFile["Directory"]["outputFolder"])


# Funções 
def searchDirectory():
	selectedDir = tkinter.filedialog.askdirectory()
	destiny.set(selectedDir)

	with open("config.ini","w") as wConfigFile:
		configFile["Directory"]["outputFolder"] = selectedDir
		configFile.write(wConfigFile)

def updateStatus():
	
	 # Get the current message
    current_status = status.get()

    # If the message is "Working...", start over with "Working"
    if current_status.endswith("..."):
    	current_status = current_status.replace("...","")

    # If not, then just add a "." on the end
    else: 
    	if current_status != "Pronto.":
    		current_status += "."

    # Update the message
    status.set(current_status)

    # After 1 second, update the status
    root.after(500, updateStatus)


def addVideos():
	global activeApiThread
	if activeApiThread.isAlive():
		tkinter.messagebox.showinfo("Alerta","Uma música ou mais ja estão sendo adicionadas")

	else:
		if link.get() == "":
			tkinter.messagebox.showinfo("Error","Por Favor digite o link de uma playlist ou video antes de tentar adicionar")
		else:
			status.set("Adicionando Videos")
			activeApiThread = GoogleApiHandler(link.get())
			activeApiThread.start()

def writeListFile():
	try:
		with open("downloadlist.pe","wb") as downFile:
			global listToDownload
			pickle.dump(listToDownload,downFile)
	except:
		pass

def readListFile():
	try:

		with open("downloadlist.pe","rb") as downFile:
			global listToDownload

			listToDownload = pickle.load(downFile)

			for item in listToDownload:
				videoList.insert(END,item)
	except:
		pass

def clearList():
	listToDownload[:] = []
	videoList.delete(0,END)
	writeListFile()

def downloadVideos():
	global activeDownloaderThread
	if activeDownloaderThread.isAlive():
		tkinter.messagebox.showinfo("Alerta","Uma música ou mais ja estão sendo baixadas")
	else:	
		if destiny.get() == "" or listToDownload == []:
			tkinter.messagebox.showinfo("Error","Por Favor escolha o destino dos arquivos ou adicione alguma música para baixar")
		else:
			status.set("Baixando videos")
			activeDownloaderThread = musicDownloader(listToDownload,destiny.get())
			activeDownloaderThread.start()

def stopDownload():
	global stopDownloadFlag

	stopDownloadFlag = True

	tkinter.messagebox.showinfo("Alerta","O Download ira parar depois que finalizar a proxima musica")

# Começo do módulo de escolher o destino dos arquivos
directoryFrame = Frame(root)
directoryFrame.grid(row=1,column=1,columnspan=3,padx=15,pady=15)

directoryLabel = Label(directoryFrame,text="Caminho \n destino",font="Verdana 10 bold")
directoryLabel.grid(row=1,column=1)

directoryEntry = Entry(directoryFrame,textvariable=destiny,width=75)
directoryEntry.grid(row=1,column=2,padx=6)

directorySearch = Button(directoryFrame,text="Procurar",command=searchDirectory)
directorySearch.grid(row=1,column=3)

# Começo do módulo de adicionar videos a lista de downloads

videoFrame = Frame(root)
videoFrame.grid(row=2,column=1,columnspan=3,padx=15,pady=15)

videoLabel = Label(videoFrame,text="Video/Playlist",font="Verdana 10 bold")
videoLabel.grid(row=1,column=1)

videoEntry = Entry(videoFrame,textvariable=link,width=75)
videoEntry.grid(row=1,column=2,padx=6)

videoAdd = Button(videoFrame,text="Adicionar",command=addVideos)
videoAdd.grid(row=1,column=3)

# Começo do módulo de adicionar videos a lista de lista

listFrame = Frame(root)
listFrame.grid(row=3,column=1,columnspan=3,padx=10,pady=30,sticky=W)

videoLabel = Label(listFrame,text="Musicas a serem baixadas",font="Verdana 8 bold")
videoLabel.grid(row=1,column=1)

videoList = Listbox(listFrame,width=130,height=20)
videoList.grid(row=2,column=1)

buttonFrame = Frame(root)
buttonFrame.grid(row=4,column=1,columnspan=3,padx=15,pady=15)

downloadButton = Button(buttonFrame,text="Baixar",command=downloadVideos)
downloadButton.grid(row=1,column=1,pady=10,padx=10)

stopButton = Button(buttonFrame, text="Parar",command=stopDownload)
stopButton.grid(row=1,column=2,pady=10,padx=10)

clearButton = Button(buttonFrame,text="Limpar",command=clearList)
clearButton.grid(row=1,column=3,pady=10,padx=10)

# Status Bar
statusBar = Label(root, bd=1, relief = SUNKEN, anchor=W,textvariable=status)
statusBar.grid(row=4,column=1,columnspan=10,sticky=S+W+E) 

root.after(1, updateStatus)
root.after(1, readListFile)


root.mainloop()
