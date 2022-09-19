import os

import axipy
from axipy import AxiomaPlugin, state_manager

from .toolprocessing.DlgBounds import DlgBounds
from .toolprocessing.utils import runOptimizationBounds


class Plugin(AxiomaPlugin):
    def load(self):
        name_observer="CountTableVector"

        self.__observer=None

        try:
            self.__observer=state_manager.find(name_observer)
        except:
            pass
        if self.__observer is None:
            self.__observer=state_manager.create(name_observer,False)
        axipy.da.data_manager.updated.connect(self.__isEvailabel)
        local_file_icon=os.path.join(os.path.dirname(os.path.realpath(__file__)),'icons', 'bound_tab.png')
        self.__action = self.create_action('Оптимизация границ таблицы',icon=local_file_icon,
                                            on_click=self.run_tools,enable_on = name_observer)

        position = self.get_position('Дополнительно', 'Инструменты')
        position.add(self.__action,size=2)
    def run_tools(self):
        dlg_bounds=DlgBounds(None,axipy.app.mainwindow.qt_object())
        dlg_bounds.show()
        if dlg_bounds.isOk:
            property_run=dlg_bounds.paramRunOptBound
            runOptimizationBounds(property_run)
    def unload(self):
        self.__action.remove()
    def __isEvailabel(self):
        def isVector(obj):
            if not isinstance(obj, axipy.Table):
                return False
            return obj.is_spatial
        vectors = list(filter( isVector, axipy.da.data_manager.objects))
        if len(vectors)>0:
            self.__observer.setValue(True)
        else:
            self.__observer.setValue(False)

