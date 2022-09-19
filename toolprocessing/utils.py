import os
import time

import axipy
from PySide2 import QtCore
from PySide2.QtWidgets import QProgressDialog
from axipy import Table, Point, Polygon, Rect, CoordSystem, Schema, provider_manager


class DoubleRect:
    __xmin=None
    __ymin=None
    __xmax=None
    __ymax=None
    def __init__(self,cs:CoordSystem,xmin=None,ymin=None,xmax=None,ymaх=None):
        self.__cs=cs
        self.__xmin=xmin
        self.__ymin=ymin
        self.__xmax=xmax
        self.__ymax=ymaх
    @property
    def xmin(self):
        return self.__xmin
    @property
    def ymin(self):
        return self.__ymin
    @property
    def xmax(self):
        return self.__xmax
    @property
    def ymax(self):
        return self.__ymax
    def merge(self,rect:Rect ):
        if rect.xmin<self.__xmin:
            self.__xmin=rect.xmin
        if rect.xmax>self.__xmax:
            self.__xmax=rect.xmax
        if rect.ymin<self.__ymin:
            self.__ymin=rect.ymin
        if rect.ymax>self.__ymax:
            self.__ymax=rect.ymax
    @property
    def coordsystem(self):
        return self.__cs
    def merge(self,rect):
        self.__merge_point(rect.xmin,rect.ymin)
        self.__merge_point(rect.xmin,rect.ymax)
        self.__merge_point(rect.xmax,rect.ymax)
        self.__merge_point(rect.xmax,rect.ymin)
    def mergePoint(self,point:Point):
        if self.__xmin is None or self.__xmax is None or self.__ymin is None or self.__ymax is None:
            self.__xmin=point.x
            self.__ymin=point.y
            self.__xmax=point.x
            self.__ymax=point.y
            return
        if point.x<self.__xmin:
            self.__xmin=point.x
        if point.x>self.__xmax:
            self.__xmax=point.x
        if point.y<self.__ymin:
            self.__ymin=point.y
        if point.y>self.__ymax:
            self.__ymax=point.y
        return
    def __merge_point(self,x,y):
        if x<self.__xmin:
            self.__xmin=x
        if x>self.__xmax:
            self.__xmax=x
        if y<self.__ymin:
            self.__ymin=y
        if y>self.__ymax:
            self.__ymax=y
        return
    def extendOnProcent(self,value_proc_ext):
        self.__xmin,self.__xmax=self.__calcExtend(value_proc_ext,self.__xmin,self.__xmax)
        self.__ymin,self.__ymax=self.__calcExtend(value_proc_ext,self.__ymin,self.__ymax)
    def __calcExtend(self,value_proc_ext,val_min,val_max):
        dx=val_max-val_min
        val_dx_proc=dx/100
        d_proc=val_dx_proc*value_proc_ext
        return val_min-d_proc,val_max+d_proc
    def reproject(self,new_cs):
        poly=Polygon.from_rect(Rect(self.__xmin,self.__ymin,self.__xmax,self.__ymax),self.__cs)
        poly_rep=poly.reproject(new_cs)
        bound=poly_rep.bounds
        return DoubleRect(new_cs,bound.xmin,bound.ymin,bound.xmax,bound.ymax)
    @property
    def clone(self):
        return DoubleRect(self.__cs,self.__xmin,self.__ymin,self.__xmax,self.__ymax)
    @property
    def boundsStr(self):
        str_bounds="Bounds ("+coordToString(self.__xmin,self.__cs.lat_lon)
        str_bounds=str_bounds+","+coordToString(self.__ymin,self.__cs.lat_lon)+") "
        str_bounds=str_bounds+"("+coordToString(self.__xmax,self.__cs.lat_lon)+","

        str_bounds=str_bounds+coordToString(self.__ymax,self.__cs.lat_lon)+")"
        return str_bounds

'''
Получения границ таблицы ( границы проекции и геометрии)
'''
def getTableBounds(table:Table,isGeometryBound=False):
    if table is None:
        return None,None
    if table.coordsystem is None:
        return None,None
    bound_cs=table.coordsystem.rect
    bound_rec_cs=DoubleRect(table.coordsystem,bound_cs.xmin,bound_cs.ymin,bound_cs.xmax,bound_cs.ymax)
    if not isGeometryBound:
        return bound_rec_cs,None
    ''' Select bound geometry from table'''
    sql="Select Max(MbrMaxX(FromAxiGeo(obj))) as xmax,Max(MbrMaxY(FromAxiGeo(obj))) as ymax,Min(MbrMinX(FromAxiGeo(obj))) as xmin,Min(MbrMinY(FromAxiGeo(obj))) as ymin From "+table.name
    tab_sel=axipy.da.data_manager.query(sql)
    fts=tab_sel.items()
    for ft in fts:
        xmin=ft['xmin']
        xmax=ft['xmax']
        ymin=ft['ymin']
        ymax=ft['ymax']
    bound_rec_geo=DoubleRect(table.coordsystem,xmin,ymin,xmax,ymax)
    tab_sel.close()
    return bound_rec_cs,bound_rec_geo
''' Формирования списка таблиц с bounds cs и geometry'''
def getListTableAndBounds(isGeometryBound=False):
    list_data=axipy.da.data_manager.tables
    bounds_info=[]
    for tab in list_data:
        if tab.provider!='TabDataProvider':
            continue
        bound_cs,bound_geo=getTableBounds(tab,isGeometryBound)
        if bound_cs is None:
            continue
        bounds_info.append({'name':tab.name,'bound_cs':bound_cs,'bound_geo':bound_geo})
    return bounds_info
def updateListTableAndBounds(listBoundsTable):
    for item_tab in listBoundsTable:
        name=item_tab['name']
        tab=axipy.app.mainwindow.catalog.find(name)
        bound_cs,bound_geo=getTableBounds(tab,True)
        item_tab['bound_geo']=bound_geo
    return
''' Форматирование координат '''
def coordToString(value,typeCsLatLon=True):
    if typeCsLatLon:
        return f'{value:0.6f}'
    else:
        return f'{value:0.2f}'
def findInListDict(data_list,name_key,value_key):
    try:
        obj_find=next(item for item in data_list if item[name_key] == value_key)
        return obj_find
    except:
        return None
def findAndDelFromListDict(data_list,name_key,value_key):
    for i,item in enumerate(data_list):
        if item[name_key]==value_key:

            return i
    return -1
def replaceBound(str_prj,rect:DoubleRect):
    index=str_prj.lower().find('bounds')
    if index<=0:
        str_bound=rect.boundsStr
        return str_prj+" "+str_bound
    temp_str=str_prj.strip()
    temp_str=temp_str[0 : index : ]
    return temp_str+" "+rect.boundsStr
def copyTable(source_tab:Table,dest_path,new_bound,progress_bar=None):
    def_buffer_size=50
    list_feture=[]
    new_prj=replaceBound(source_tab.coordsystem.prj,new_bound)
    new_coordsys=CoordSystem.from_prj(new_prj)
    schema_source=Schema(source_tab.schema.copy(),new_coordsys)
    '''
    cs_source=schema_source.coordsystem
    cs_prj=cs_source.prj
    new_prj=replaceBound(cs_prj,new_bound)
    #cs_source.rect.xmin=new_bound.xmin
    cs_source.rect=new_bound
    '''
    def_tab={'src':dest_path,'schema':schema_source,'hidden':True}
    table = provider_manager.create(def_tab)
    if progress_bar is not None:
        start_count=progress_bar.value()
        progress_bar.setLabelText("Таблица "+source_tab.name)
    isCancel=False
    for ft in source_tab.items():
        list_feture.append(ft)
        if progress_bar is not None:
            time.sleep(0.001)
            if progress_bar.wasCanceled():
                isCancel=True
                break
            progress_bar.setValue(progress_bar.value()+1)

        if len(list_feture)>def_buffer_size:
            table.insert(list_feture)
            list_feture.clear()
    if isCancel:
        table.restore()
        table.close()
        return isCancel
    if len(list_feture)>0:
        table.insert(list_feture)
    table.commit()
    table.close()
    return isCancel
def runOptimizationBounds(param_run):
    out_bound=param_run['opt_bounds']
    list_name_tab=param_run['name_tables']
    def_ext_tab=param_run['ext_tab']
    path_out=param_run['out_path']
    count_all_ft=0
    for tab in list_name_tab:
        table=axipy.app.mainwindow.catalog.find(tab['name'])
        count_all_ft=count_all_ft+table.count()
    cls_progressbar = QProgressDialog(axipy.app.mainwindow.qt_object())

    cls_progressbar.setWindowModality(QtCore.Qt.ApplicationModal)
    cls_progressbar.setWindowFlags(
        cls_progressbar.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint)
    cls_progressbar.setWindowTitle("Оптимизация границ")
    cls_progressbar.setLabelText("Таблица "+list_name_tab[0]['name'])
    #  progdialog.canceled.connect(self.close)
    cls_progressbar.setRange(0, count_all_ft)
    cls_progressbar.show()
    for tab in list_name_tab:
        curent_path_out=path_out
        if len(list_name_tab)>1:
            curent_path_out=os.path.join(path_out,tab['name']+def_ext_tab+".tab")
        table=axipy.app.mainwindow.catalog.find(tab['name'])
        isCancel=copyTable(table,curent_path_out,out_bound,cls_progressbar)
        if isCancel:
            break
    cls_progressbar.close()



