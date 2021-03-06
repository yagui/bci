from scipy import signal #proc de segnales
import numpy as np #vectores, operaciones matematicas
import time
import config
from multiprocess_config import *
from signal_processing_config import *
#[b_spike,a_spike]=signal.iirfilter(4,[float(300*2)/config.FS, float(6000*2)/config.FS], rp=None, rs=None, btype='band', analog=False, ftype='butter',output='ba')


filter_coef=signal.firwin(length_bandpass, [float(Fmin*2)/config.FS,float(Fmax*2)/config.FS], width=None, window=window_type, pass_zero=False)
group_delay=((length_bandpass-1)/2)*(length_bandpass%2)+(length_bandpass+1)%2*(length_bandpass/2)


#MEAN_L=5  #ESTO PODRIA PONERSE A BASE DE TIEMPO

#def calcular_umbral_disparo(data,canales):
    #x=abs(signal.lfilter(b_spike,a_spike,data[canales,:]))
    #umbrales=4*np.median(x/0.6745,1)
    #return x,umbrales
    
#def calcular_tasa_disparo(x,umbral):
    #t1=time.time()
    #if umbral >= 0:
        #pasa_umbral=(x>umbral)
    #else:
        #pasa_umbral=(x<umbral)
    #np.sum(pasa_umbral[:-1] * ~ pasa_umbral[1:])
    #print time.time()-t1

#def spikes_detect(x,umbral):
#    b=np.matrix(x*np.sign(umbral)>np.abs(umbral),np.int)        
#    b=np.diff(b,1,1)
#    aux=np.nonzero(b)
#    new_spikes_times=list([[] for i in range(config.CANT_CANALES)])
#    for i in range(aux[0].size):
#        new_spikes_times[aux[0][0,i]].append(aux[1][0,i])
#    
#    return new_spikes_times
#    
def spikes_detect(x,umbral):
    new_spikes_times=list()
    #aux=[]
    for i in range(config.CANT_CANALES):
#        if(umbral[i]>0):
#            aux=np.nonzero(np.ediff1d(x[i,:]>umbral[i], to_end=None, to_begin=None)) 
#        else:
#            aux=np.nonzero(np.ediff1d(x[i,:]<umbral[i], to_end=None, to_begin=None))
#        new_spikes_times.append(aux)
        if(umbral[i]>0):
                aux=np.less(x[i,:],umbral[i])
        else:
                aux=np.greater(x[i,:],umbral[i])
        new_spikes_times.append(np.nonzero(aux[1:].__and__(~aux[:-1])))    
        
        
        #aux=[]
#        if(umbral[i]>0):
#            #aux=np.nonzero(np.ediff1d(x[i,:]>umbrales[i], to_end=None, to_begin=None)) 
#            new_spikes_times.append(np.nonzero(np.ediff1d(np.sign(x[i,:]>umbral[i]), to_end=None, to_begin=None)>0) )
#        else:
#            new_spikes_times.append(np.nonzero(np.ediff1d(np.sign(x[i,:]<umbral[i]), to_end=None, to_begin=None)>0) )
            #aux=np.nonzero(np.ediff1d(x[i,:]<umbrales[i], to_end=None, to_begin=None))
        
    
    return new_spikes_times
    
def data_processing(data_queue,ui_config_queue,graph_data_queue,proccesing_control,warnings):
    #import config
    graph_data=Data_proc2ui()
    control=''
#    mean_calc=np.int16(np.zeros([config.CANT_CANALES,MEAN_L]))
#    mean_l=0
#    mean_aux=np.ndarray([config.CANT_CANALES,1])
    new_data=np.ndarray([config.CANT_CANALES,config.PAQ_USB+length_bandpass-1],np.uint16)
    while(control != EXIT_SIGNAL):
        while not proccesing_control.poll():
            if not ui_config_queue.empty():
                try:
                    ui_config=ui_config_queue.get(TIMEOUT_GET)
                except:
                    pass
            try:
                new_data[:,length_bandpass-1:]=data_queue.get(TIMEOUT_GET)
            except:
                continue
            #filtar y enviar si filtro activo en conf o bien asi como esta
#            np.mean(new_data[:,length_bandpass-1:],1,out=mean_calc[:,mean_l])
#            mean_l+=1
#            if mean_l is MEAN_L :
#                mean_l=0
#            
#            np.mean(mean_calc,1,out=mean_aux)
#            #casa falta muucho 
#            new_data[:,length_bandpass-1:]=new_data[:,length_bandpass-1:]-mean_aux
            
            
            filtered_data=signal.lfilter(filter_coef,1,new_data)[:,length_bandpass-1:] #casa terriblemente mal no tiene en cuenta nada
                
            spikes_times=spikes_detect(filtered_data,ui_config.thresholds)
            #casa ojo la fase lineal q desplaza todo
            

            graph_data.spikes_times=spikes_times
            
            if ui_config.filter_mode is True:
                graph_data.new_data=filtered_data
                graph_data.filter_mode=True
            else:
                graph_data.new_data=new_data[:,length_bandpass-1:]
                graph_data.filter_mode=False
            try:
                graph_data_queue.put_nowait(graph_data)
            except:
                try:
                    warnings.put_nowait(SLOW_GRAPHICS_SIGNAL) 
                except:
                    pass
            new_data[:,:length_bandpass-1]=new_data[:,-length_bandpass+1:]
        
        control=proccesing_control.recv()
        #FER falta la opcion iniciar sorting usando la pipe q hace q se cierre el proceso para transportar la info
       #numpy.where !!!
       

class Data_proc2ui():
    def __init__(self):
        self.new_data=0
        self.spikes_times=np.zeros([0])
        self.filter_mode=False
        #aca podria cambiar de filtro con un aviso para el recalculo.. aunq afectaria el sorting
