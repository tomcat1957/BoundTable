import os
from pathlib import Path

import axipy
from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtGui import Qt, QIntValidator, QIcon
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog, QTableWidgetItem, QSlider, QFileDialog
from axipy.app import Notifications

from BoundTable.toolprocessing.utils import coordToString, findInListDict, findAndDelFromListDict, \
    getListTableAndBounds, updateListTableAndBounds


class DlgBounds(QDialog):
    __def_max_proc=5
    __def_prfix_out="_opt"
    __isEditBounds=False
    __isNotGeometryBounds=True
    def __init__(self,list_table_inp,parent=None):
        self.__data=list_table_inp
        self.__parent=parent
        if list_table_inp is None:
            self.__data=getListTableAndBounds()

        self.__list_select_tab=[]
        self.load_ui()
        self.__ui.setWindowFlags(
            self.__ui.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.__ui.tableView.setColumnCount(5)
        cont_row=len(self.__data)
        self.__ui.tableView.setRowCount(cont_row)
        self.__ui.tableView.setColumnWidth(0, 100)
        self.__ui.tableView.setColumnWidth(1, 80)
        self.__ui.tableView.setColumnWidth(2, 80)
        self.__ui.tableView.setColumnWidth(3, 80)
        self.__ui.tableView.setColumnWidth(4, 80)
        self.__loadTable('bound_cs')
        self.__ui.tableView.itemClicked.connect(self.__handleItemClicked)
        self.__ui.tableView.resizeColumnsToContents()
        self.__ui.ch_box_bounds_type.stateChanged.connect(self.__click_ch_bounds)
        int_validator=QIntValidator(0,5)
        self.__ui.ln_edit_proc.setValidator(int_validator)
        self.__ui.ln_edit_proc.textChanged.connect(self.__change_proc_bound)
        '''
        self.__ui.hz_slider.setMinimum(0)
        self.__ui.hz_slider.setMaximum(50)
        self.__ui.hz_slider.setRange(0, 50)
        self.__ui.hz_slider.setSingleStep(1)
        self.__ui.hz_slider.setTickInterval(2)
        self.__ui.hz_slider.setValue(0)
        self.__ui.hz_slider.setTickPosition(QSlider.TicksBelow)
        self.__ui.hz_slider.setInvertedAppearance(True)
        self.__ui.hz_slider.setInvertedControls(True)
        '''
        self.__ui.hz_slider.valueChanged.connect(self.__change_proc)
        self.__ui.pb_change_path.clicked.connect(self.__select_out_path)
        self.__ui.pb_recalc.clicked.connect(self.__recalc_bound)
        #pb_run
        #icon=QIcon("save_as_32.png")
        self.__ui.pb_change_path.setIcon(QIcon("icon/saveas.png"))
        self.__ui.pb_close.clicked.connect(self.__close_dlg)
        self.__ui.pb_run.clicked.connect(self.__run)
    def __handleItemClicked(self,item):
        id_column=item.column()
        if id_column>0:
            return
        name_tab=item.text()
        if item.checkState() == QtCore.Qt.Checked:
            tab_bound_sel=findInListDict(self.__data,'name',name_tab)
            if tab_bound_sel is None:
                return
            if len(self.__list_select_tab)>0 and (self.__list_select_tab[0]['bound_cs'].coordsystem.name!=tab_bound_sel['bound_cs'].coordsystem.name):
                item.setCheckState(QtCore.Qt.Unchecked)
                Notifications.push('Предупреждение', 'Проекция таблицы '+name_tab+' отличается от базовой', Notifications.Warning)
                return
            self.__list_select_tab.append(tab_bound_sel)
            if len(self.__list_select_tab)==1:
                self.__ui.lb_name_tab.setText(name_tab)
                self.__ui.lb_base_cs.setText(tab_bound_sel['bound_cs'].coordsystem.name)
                self.__create_out_path(self.__list_select_tab[0]['name'])
                self.__ui.ln_out_path.setText(self.__getPathOut())
        else:
            if len(self.__list_select_tab)==0:
                return
            indexDel=findAndDelFromListDict(self.__list_select_tab,'name',name_tab)
            self.__list_select_tab.pop(indexDel)
            if len(self.__list_select_tab)==0:
                self.__ui.lb_name_tab.setText("")
                self.__ui.lb_base_cs.setText("")
            else:
                if indexDel==0:
                    self.__ui.lb_name_tab.setText(self.__list_select_tab[0]['name'])
                    self.__ui.lb_base_cs.setText(self.__list_select_tab[0]['bound_cs'].coordsystem.name)


        if(len(self.__list_select_tab)>0):
            self.__create_out_path(self.__list_select_tab[0]['name'])
            self.__ui.ln_out_path.setText(self.__getPathOut())
            self.__ui.gb_out.setEnabled(True)
            self.__ui.pb_run.setEnabled(True)
        else:
            self.__ui.ln_out_path.setText("")
            self.__ui.gb_out.setEnabled(False)
            self.__ui.pb_run.setEnabled(False)
        self.__updateMergerBound()
    def __create_out_path(self,name_table):
        table_base=axipy.app.mainwindow.catalog.find(name_table)
        try:
            path_tab=table_base.properties['tabFile']
        except:
            path_tab=str(Path.home())
            path_tab=os.path.join(path_tab,name_table+".tab")
        self.__base_out_path=path_tab
    def __getPathOut(self):
        if len(self.__list_select_tab)>1:
            ''' Формируем директорию'''
            return str(Path(self.__base_out_path).parent)
        else:
            ''' Выбрана одна таблица '''
            out_path=str(Path(self.__base_out_path).parent)
            name=str(Path(self.__base_out_path).stem)+self.__def_prfix_out+".tab"
            return os.path.join(out_path,name)
    def __select_out_path(self):
        if len(self.__list_select_tab)>1:
            ''' Выбираем директорию '''
            base_folder=str(Path(self.__base_out_path).parent)
            dir_path=QFileDialog.getExistingDirectory(self.__ui,"Выбирите директорию для сохранения таблиц",base_folder)
            if dir_path!='':
                self.__ui.ln_out_path.setText(dir_path)
        else:
            ext_files = "MapInfo tab (*.tab)"
            name_load_file = QFileDialog.getSaveFileName(self.__ui, 'Сохранить tab',self.__base_out_path, ext_files)
        #options = QFileDialog.DontConfirmOverwrite)
            if name_load_file is None:
                return
            file_tab=name_load_file[0]
            if file_tab!='':
                self.__ui.ln_out_path.setText(file_tab)
    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "DlgBounds.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.__ui  = loader.load(ui_file,self.__parent)
        ui_file.close()
    def __clearTable(self):
        while (self.__ui.tableView.rowCount() > 0):

            self.__ui.tableView.removeRow(0)
    def __change_proc_bound(self):
        str_value=self.__ui.ln_edit_proc.text()
        value=float(str_value)
        if value==0:
            self.__outBoundToGui(self.__merge_rect)
            self.__ui.pb_recalc.setEnabled(False)
            self.__ui.hz_slider.setValue(0)
        else:
            int_val_slider=int(value*10)
            self.__ui.hz_slider.setValue(int_val_slider)

    def __click_ch_bounds(self):
        #self.__clearTable()
        if self.__ui.ch_box_bounds_type.isChecked():
            if self.__isNotGeometryBounds:
                updateListTableAndBounds(self.__data)
                self.__isNotGeometryBounds=False
            self.__loadTable('bound_geo')

        else:
            self.__loadTable('bound_cs')
        self.__ui.tableView.resizeColumnsToContents()
        if len(self.__list_select_tab)>0:
            for i in range(self.__ui.tableView.rowCount()):
                item=self.__ui.tableView.item(i,0)
                name=item.text()
                obj_sel=tab_bound_sel=findInListDict(self.__list_select_tab,'name',name)
                if obj_sel is not None:
                    item.setCheckState(QtCore.Qt.Checked)
            self.__updateMergerBound()

    def __change_proc(self):
        value_int=self.__ui.hz_slider.value()
        procent_inc=value_int/10
        self.__ui.ln_edit_proc.setText(str(procent_inc))
        if value_int==0:
            self.__outBoundToGui(self.__merge_rect)
            self.__ui.pb_recalc.setEnabled(False)
            return
        self.__isEditBounds=True
        self.__ui.pb_recalc.setEnabled(True)
        self.__curent_merge_rect=self.__merge_rect.clone
        self.__curent_merge_rect.extendOnProcent(procent_inc)
        self.__outBoundToGui(self.__curent_merge_rect)
    def __createRowBounds(self,value):
        r_col=QTableWidgetItem(str(value))
        r_col.setTextAlignment(Qt.AlignRight)
        return r_col
    def __recalc_bound(self):
        self.__ui.hz_slider.setValue(0)
        self.__ui.ln_edit_proc.setText("0")
        self.__updateMergerBound()
    def __loadTable(self,name_data):
        for i,tab in enumerate(self.__data):
            bound_cs=tab[name_data]
            r_col_name=QTableWidgetItem(tab['name'])
            r_col_name.setFlags(QtCore.Qt.ItemIsUserCheckable |
                             QtCore.Qt.ItemIsEnabled)
            r_col_name.setCheckState(QtCore.Qt.Unchecked)
            self.__ui.tableView.setItem(i,0,r_col_name)
            self.__ui.tableView.setItem(i,1,self.__createRowBounds(coordToString(bound_cs.xmin,bound_cs.coordsystem.lat_lon)))
            self.__ui.tableView.setItem(i,2,self.__createRowBounds(coordToString(bound_cs.ymin,bound_cs.coordsystem.lat_lon)))
            self.__ui.tableView.setItem(i,3,self.__createRowBounds(coordToString(bound_cs.xmax,bound_cs.coordsystem.lat_lon)))
            self.__ui.tableView.setItem(i,4,self.__createRowBounds(coordToString(bound_cs.ymax,bound_cs.coordsystem.lat_lon)))
    def __outBoundToGui(self,rect):
        self.__ui.ln_xmin.setText(coordToString(rect.xmin,rect.coordsystem.lat_lon))
        self.__ui.ln_ymin.setText(coordToString(rect.ymin,rect.coordsystem.lat_lon))
        self.__ui.ln_xmax.setText(coordToString(rect.xmax,rect.coordsystem.lat_lon))
        self.__ui.ln_ymax.setText(coordToString(rect.ymax,rect.coordsystem.lat_lon))
    def __updateMergerBound(self):
        if self.__list_select_tab is None or len(self.__list_select_tab)==0:
            self.__ui.groupBox_MergeBound.setEnabled(False)
            self.__ui.ln_xmin.setText("0")
            self.__ui.ln_ymin.setText("0")
            self.__ui.ln_xmax.setText("0")
            self.__ui.ln_ymax.setText("0")
            return
        name_bounds='bound_cs'
        if self.__ui.ch_box_bounds_type.isChecked():
            name_bounds='bound_geo'
        self.__merge_rect=self.__list_select_tab[0][name_bounds].clone
        if len(self.__list_select_tab)==1:
            self.__outBoundToGui(self.__merge_rect)
            self.__ui.groupBox_MergeBound.setEnabled(True)
            return
        for i in range(1,len(self.__list_select_tab)):
            self.__merge_rect.merge(self.__list_select_tab[i][name_bounds])
        self.__outBoundToGui(self.__merge_rect)
        self.__ui.groupBox_MergeBound.setEnabled(True)
        return
    def __close_dlg(self):
        self.__isOk=False
        self.__ui.close()
    def __run(self):
        self.__isOk=True
        self.__ui.close()
    @property
    def paramRunOptBound(self):
        params={}
        params['name_tables']=self.__list_select_tab
        params['out_path']=self.__ui.ln_out_path.text()
        if self.__isEditBounds:
            params['opt_bounds']=self.__curent_merge_rect
        else:
            params['opt_bounds']=self.__merge_rect
        params['ext_tab']=self.__def_prfix_out
        return params
    @property
    def isOk(self):
        return self.__isOk
    def show(self):
        self.__ui.exec()