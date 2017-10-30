from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from ptsa.data.readers import *
from ptsa.data.filters import *
from ptsa.data.readers.IndexReader import JsonIndexReader
import numpy as np
from scipy.signal import butter, filtfilt, freqz
import sys
pg.setConfigOption('background', 'w')  # Change background and foreground of plots
pg.setConfigOption('foreground', 'k')
# plt.switch_backend('Qt5Agg')

global buffer
buffer = 0  # Initialize buffer
mb = 0  # Initialize mono-bi state dummy variable


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        # USED TO INIITALIZE THE GUI DO NOT ALTER
        super(Ui, self).__init__()
        uic.loadUi('EEG_Vis_1.ui', self)  # Load Designer File MAKE SURE IS IN SAME DIRECTORY AS THIS SCRIPT
        self.initui()
        self.showMaximized()  # Full screen
        pg.setConfigOption('useWeave', True)  # Use weave to optimize some processes
        pg.setConfigOption('weaveDebug', True)

    def initui(self):
        self.e_ind = 0
        self.setWindowTitle("EEG Visualizer")
        # CONNECT FUNCTIONS AND HOTKEYS TO UI WIDGETS
        # TAB 1
        self.EventSearch.clicked.connect(self.search_event)  # Event search button
        self.TalSearch.clicked.connect(self.search_tal)  # Tal search button
        self.RhinoButton.clicked.connect(self.find_rhino)  # Locate Rhino Root for JSON
        self.JsonLoad.clicked.connect(self.load_json)  # Json load button
        self.TypesList.itemSelectionChanged.connect(self.select_type)  # Select type
        #self.AttrList.itemSelectionChanged.connect(self.select_attr)  # Select attribute
        self.ElectrodeList.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Multiple selections allowed
        self.ElectrodeList.itemSelectionChanged.connect(self.select_electrodes)  # Select electrodes
        self.EEGButton.clicked.connect(self.load_eeg)  # Load EEG session
        self.FilterButton.clicked.connect(self.run_filter)  # Run selected filter
        self.RemoveButton.clicked.connect(self.unapply_filter)  # Remove selected filter
        self.RemoveAllButton.clicked.connect(self.remove_filter)  # Remove applied filters
        self.SessionIndex.currentIndexChanged.connect(self.change_session)  # Changes session to be loaded
        self.EventIndex.valueChanged.connect(self.get_ind)  # Get value of index
        self.LoadKey = QShortcut(QKeySequence("Ctrl+1"), self)  # Change tab hotkeys
        self.MonoBiGroup = QButtonGroup()
        self.MonoBiGroup.addButton(self.BiButton)
        self.MonoBiGroup.addButton(self.MonoButton)
        self.MonoButton.setChecked(True)
        self.DsGroup = QButtonGroup()
        self.DsGroup.addButton(self.Downsample_1)
        self.DsGroup.addButton(self.Downsample_2)
        self.Downsample_1.setChecked(True)


        # TAB 2
        self.AnnPlotList.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Multiple selections allowed
        self.AnnPlotList.itemSelectionChanged.connect(self.select_annotations)  # Select event types to annotate
        self.RemoveChanList.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Multiple selections allowed
        self.AnnPlotButton.clicked.connect(self.view_annotations)  # Update annotations on graphs
        self.ClearAnnButton.clicked.connect(self.clear_annotations)  # Clear annotations
        self.RemoveChanButton.clicked.connect(self.remove_channels)  # Remove channels from view
        self.ViewButton.clicked.connect(self.reset_view)  # Plot reset view
        self.ViewButtonKey = QShortcut(QKeySequence("Ctrl+X"), self)  # View all hotkey
        self.ViewButtonKey.activated.connect(self.reset_view)
        self.HorizontalBox.clicked.connect(self.toggle_horizontal)  # Change horizontal scrolling
        self.HorizontalKey = QShortcut(QKeySequence("Ctrl+D"), self)  # Horizontal scrolling hotkey
        self.HorizontalKey.activated.connect(self.iso_horizontal)
        self.VerticalBox.clicked.connect(self.toggle_vertical)  # Change vertical scrolling
        self.VerticalKey = QShortcut(QKeySequence("Ctrl+S"), self)  # Vertical scrolling hotkey
        self.VerticalKey.activated.connect(self.iso_vertical)
        self.BothKey = QShortcut(QKeySequence("Ctrl+F"), self)
        self.BothKey.activated.connect(self.zoom_both)
        self.BoxZoomBox.clicked.connect(self.box_zoom)  # Toggle box zoom
        self.BoxZoomKey = QShortcut(QKeySequence("Ctrl+A"), self)  # Box zoom hotkey
        self.BoxZoomKey.activated.connect(self.box_hotkey)
        self.MarkEventKey = QShortcut(QKeySequence("Ctrl+M"), self)
        self.MarkEventKey.activated.connect(self.mark_event)
        self.MarkBadButton.clicked.connect(self.mark_bad)  # Append to text file
        self.DefaultButton.clicked.connect(self.mark_default)
        self.TextButton.clicked.connect(self.name_change)
        self.TextDirectorySearch.clicked.connect(self.path_change)
        self.Tab1Key = QShortcut(QKeySequence("Ctrl+Q"), self)  # Change tab hotkeys
        self.Tab2Key = QShortcut(QKeySequence("Ctrl+W"), self)  # Change tab hotkeys
        self.Tab3Key = QShortcut(QKeySequence("Ctrl+E"), self)  # Change tab hotkeys
        self.Tab1Key.activated.connect(self.tab1)
        self.Tab2Key.activated.connect(self.tab2)
        self.Tab3Key.activated.connect(self.tab3)
        self.PlotKey = QShortcut(QKeySequence("Ctrl+2"), self)  # Change tab hotkeys
        self.LoadKey.activated.connect(self.loadtab)
        self.PlotKey.activated.connect(self.plottab)
        self.UpKey = QShortcut(QKeySequence("Ctrl+Up"), self)  # Pan with arrow hotkeys
        self.UpKey.activated.connect(self.pan_up)
        self.PageUpKey = QShortcut(QKeySequence("Ctrl+Shift+Up"), self)
        self.PageUpKey.activated.connect(self.page_up)
        self.DownKey = QShortcut(QKeySequence("Ctrl+Down"), self)
        self.DownKey.activated.connect(self.pan_down)
        self.PageDownKey = QShortcut(QKeySequence("Ctrl+Shift+Down"), self)
        self.PageDownKey.activated.connect(self.page_down)
        self.LeftKey = QShortcut(QKeySequence("Ctrl+Left"), self)
        self.LeftKey.activated.connect(self.pan_left)
        self.PageLeftKey = QShortcut(QKeySequence("Ctrl+Shift+Left"), self)
        self.PageLeftKey.activated.connect(self.page_left)
        self.RightKey = QShortcut(QKeySequence("Ctrl+Right"), self)
        self.RightKey.activated.connect(self.pan_right)
        self.PageRightKey = QShortcut(QKeySequence("Ctrl+Shift+Right"), self)
        self.PageRightKey.activated.connect(self.page_right)
        self.EventScrollBox.currentIndexChanged.connect(self.filter_event_scroll)
        self.EventScrollUp = QShortcut(QKeySequence("Ctrl+]"), self)  # Scrolling by event index
        self.EventScrollDown = QShortcut(QKeySequence("Ctrl+["), self)
        self.EventScrollUp.activated.connect(self.event_scroll_up)
        self.EventScrollDown.activated.connect(self.event_scroll_down)
        self.EventScroll.valueChanged.connect(self.filter_event_scroll)
        self.ZoomInKey = QShortcut(QKeySequence("Ctrl+="), self)  # Zoom in/out with hotkeys
        self.ZoomOutKey = QShortcut(QKeySequence("Ctrl+-"), self)
        self.ZoomInKey.activated.connect(self.zoom_in)
        self.ZoomOutKey.activated.connect(self.zoom_out)
        self.WindowLength.returnPressed.connect(self.change_window)
        self.TimeScroll.returnPressed.connect(self.time_scroll)
        # self.UndoKey = QShortcut(QKeySequence("Ctrl+Z"), self)
        # self.UndoKey.activated.connect(self.undo_zoom)
        # self.UndoZoomButton.clicked.connect(self.undo_zoom)
        # self.GainBox.valueChanged.connect(self.change_gain)  # Gain changer

        self.ErrorMessage.setStyleSheet('color: red')  # Change error message text to red
        self.statusBar().setStyleSheet(
            "QStatusBar{padding-left:8px;background:rgba(0,0,0,255);color:red;font-weight:bold;}")  # Change error bar

        # INITIALIZE PLOTS WITH AXES AND LEGENDS
        axes1 = {'left': 'Normalized magnitude', 'bottom': 'Time (sec)'}
        axes2 = {'left': 'Voltage (Microvolts)', 'bottom': 'Time (sec)'}
        self.plot1 = pg.PlotWidget(labels=axes2)
        self.Plot1Layout.addWidget(self.plot1)
        self.plot2 = pg.PlotWidget(labels=axes2)
        self.Plot2Layout.addWidget(self.plot2)
        self.leg2 = self.plot2.addLegend()
        self.plot3 = pg.PlotWidget(labels=axes1)
        self.Plot3Layout.addWidget(self.plot3)
        self.plot1.plotItem.ctrlMenu = None  # get rid of 'Plot Options'
        # self.plot1.scene().contextMenu = None  # get rid of 'Export'
        self.plot2.plotItem.ctrlMenu = None  # get rid of 'Plot Options'
        # self.plot2.scene().contextMenu = None  # get rid of 'Export'
        self.plot3.plotItem.ctrlMenu = None  # get rid of 'Plot Options'
        # self.plot3.scene().contextMenu = None  # get rid of 'Export'
        self.viewbox1 = self.plot1.getViewBox()  # Obtain viewbox plot objects to further manipulate them
        self.viewbox2 = self.plot2.getViewBox()
        self.viewbox3 = self.plot3.getViewBox()

    def search_event(self):
        # SEARCH FOR EVENT .MAT FILES
        options = QFileDialog.Options()  # Prompt directory search
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Search for an Event file", "",
                                                   "Matrix Files (*.mat);;All Files (*)", options=options)
        if 'event' in file_name:
            file_name = str(file_name)
            if self.RerefBox.isChecked():  # Use rereferenced data for scalp EEGs
                reref = True
            else:
                reref = False
            self.base_events = BaseEventReader(filename=file_name, use_reref_eeg=reref).read()  # Load base events
            base_event_filt = None  # Un-define data type selection
            event_types = np.unique(self.base_events.type)  # Load event types
            self.type_index = self.base_events.dtype.names.index('type')
            self.eeg_index = self.base_events.dtype.names.index('eegfile')  # Find part of event struct that defines eeg file
            self.offset_index = self.base_events.dtype.names.index('eegoffset')  # Find part of even struct that defines offsets
            self.number_of_sessions = np.unique(self.base_events.session)  # Find number of sessions
            string_sessions = map(str, self.number_of_sessions)  # Convert that list to a string
            self.SessionIndex.clear()
            self.SessionIndex.addItems(string_sessions)  # Create dropdown list with session numbers
            self.session_no = eval(self.SessionIndex.currentText())  # Current session index
            self.eeg = self.base_events[self.base_events.session == self.session_no][0][self.eeg_index]  # Get EEG path from session
            self.EEGLabel.setText(self.eeg)  # Update UI text
            self.TypesList.clear()  # Clear list and populate it with data types
            all_types = QListWidgetItem("ALL TYPES")
            self.TypesList.addItem(all_types)
            self.AnnPlotList.clear()  # Clear list
            for count in range(np.size(event_types)):
                item = QListWidgetItem(event_types[count])
                self.TypesList.addItem(item)
                item = QListWidgetItem(event_types[count])
                self.AnnPlotList.addItem(item)
            self.EventScrollBox.clear()
            self.EventScrollBox.addItem("ALL TYPES")
            self.EventScrollBox.addItems(event_types)
            self.attributes = self.base_events.dtype.names
            self.AttrList.clear()  # Clear list and populate it with attributes
            for count in range(np.size(self.attributes)):
                item = QListWidgetItem(self.attributes[count])
                self.AttrList.addItem(item)
            self.directory_index = self.eeg.index("reref")
            self.directory = self.eeg[0:self.directory_index + 6]
            self.EventLabel.setText(file_name)
            self.statusBar().clearMessage()
        else:
            self.statusBar().showMessage('Load a proper event file', 6000)

    def search_tal(self):
        # SEARCH FOR TAL STRUCT .MAT FILE
        options = QFileDialog.Options()  # Prompt directory search
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Search for a Tal file", "",
                                                   "Matrix Files (*.mat);;All Files (*)", options=options)
        if 'talLocs' in file_name:
            file_name = str(file_name)
            if 'monopol.mat' in file_name:  # Load monopol
                tal_reader = TalReader(filename=file_name, struct_name='talStruct')
                self.tal_structs = tal_reader.read()
                self.monopolar_channels = np.array(['{:03d}'.format(c) for c in self.tal_structs['channel']], dtype='|S3')
                self.bipolar_pairs = None  # No bipolar pairs in monopol data
                self.mb = 'm'  # Indicator that monopolar has been loaded
                self.chaninput = 'channels'  # For telling EEG loader to read monopolar data
            elif 'bipol.mat' in file_name:  # Load bipol
                tal_reader = TalReader(filename=file_name, struct_name='bpTalStruct')
                self.tal_structs = tal_reader.read()
                self.monopolar_channels = tal_reader.get_monopolar_channels()
                self.bipolar_pairs = tal_reader.get_bipolar_pairs()
                self.mb = 'b'  # Indicator that bipolar has been loaded
                self.chaninput = 'bipolar_pairs'  # Tells EEG to load bipolar differences
            self.tagnames = self.tal_structs['tagName']  # Electrode names
            channels = self.tal_structs['channel']  # Channel names
            self.ElectrodeList.clear()  # Clear list and populate with electrode info
            all_electrodes = QListWidgetItem("ALL ELECTRODES")
            self.ElectrodeList.addItem(all_electrodes)  # First item in list is all electrodes
            for count in range(np.size(self.tagnames)):
                item = QListWidgetItem(str(channels[count]) + ': ' + self.tagnames[count])
                self.ElectrodeList.addItem(item)
            self.TalLabel.setText(file_name)
            self.statusBar().clearMessage()
        else:
            self.statusBar().showMessage('Load a proper tal file', 6000)

    def find_rhino(self):
        rhino_root = str(QFileDialog.getExistingDirectory(self, "Select RHINO Root Directory"))
        try:
            self.jr = JsonIndexReader(rhino_root + '/protocols/r1.json')  # Build JSON reader
        except:
            pass

    def load_json(self):
        # LOAD STRUCTS USING JSON INSTEAD
        try:
            self.jr  # Make sure JSON protocol has been loaded
        except:
            self.statusBar().showMessage('Locate a RHINO root to use JSON', 6000)
        else:
            if self.RerefBox.isChecked():
                reref = True
            else:
                reref = False
            self.jr_subject = self.JsonSub.text()  # Subject - CASE SENSITIVE
            self.jr_experiment = self.JsonExp.text()  # Experiment - CASE SENSITIVE
            #  LOAD EVENTS
            try:
                self.base_events = (np.concatenate([BaseEventReader(filename=f, use_reref_eeg=reref).read() for f in
                                                    self.jr.aggregate_values('task_events', subject=self.jr_subject,
                                                                             experiment=self.jr_experiment)]).view(
                    np.recarray))
                base_event_filt = None  # Un-define data type selection
                event_types = np.unique(self.base_events.type)  # Load event types
                self.type_index = self.base_events.dtype.names.index('type')
                self.eeg_index = self.base_events.dtype.names.index(
                    'eegfile')  # Find part of event struct that defines eeg file
                self.offset_index = self.base_events.dtype.names.index(
                    'eegoffset')  # Find part of even struct that defines offsets
                self.number_of_sessions = np.unique(self.base_events.session)  # Find number of sessions
                string_sessions = map(str, self.number_of_sessions)  # Convert that list to a string
                self.SessionIndex.clear()
                self.SessionIndex.addItems(string_sessions)  # Create dropdown list with session numbers
                self.session_no = eval(self.SessionIndex.currentText())  # Current session index
                self.eeg = self.base_events[self.base_events.session == self.session_no][0][
                    self.eeg_index]  # Get EEG path from session
                self.EEGLabel.setText(self.eeg)  # Update UI text
                self.TypesList.clear()  # Clear list and populate it with data types
                all_types = QListWidgetItem("ALL TYPES")
                self.TypesList.addItem(all_types)
                self.AnnPlotList.clear()  # Clear list
                for count in range(np.size(event_types)):
                    item = QListWidgetItem(event_types[count])
                    self.TypesList.addItem(item)
                    item = QListWidgetItem(event_types[count])
                    self.AnnPlotList.addItem(item)
                self.EventScrollBox.clear()
                self.EventScrollBox.addItem("ALL TYPES")
                self.EventScrollBox.addItems(event_types)
                self.attributes = self.base_events.dtype.names
                self.AttrList.clear()  # Clear list and populate it with attributes
                for count in range(np.size(self.attributes)):
                    item = QListWidgetItem(self.attributes[count])
                    self.AttrList.addItem(item)

                # LOAD TAL STRUCT
                pairs_path = self.jr.get_value('pairs', subject=self.jr_subject, experiment=self.jr_experiment)
                tal_reader = TalReader(filename=pairs_path)
                self.monopolar_channels = tal_reader.get_monopolar_channels()
                self.bipolar_pairs = tal_reader.get_bipolar_pairs()
                self.tal_structs = tal_reader.read()
                self.tagnames = self.tal_structs['tagName']
                if self.MonoButton.isChecked():
                    self.chaninput = 'channels'
                    channels = self.monopolar_channels
                    self.mb = 'm'
                else:
                    self.chaninput = 'bipolar_pairs'
                    channels = self.bipolar_pairs
                    self.mb = 'b'
                # channels = tal_structs['channel']
                self.ElectrodeList.clear()  # Clear list and populate with electrode info
                all_electrodes = QListWidgetItem("ALL ELECTRODES")
                self.ElectrodeList.addItem(all_electrodes)
                for count in range(np.size(channels)):
                    # item = QListWidgetItem(str(channels[count]) + ': ' + tagnames[count])
                    item = QListWidgetItem(str(channels[count]))
                    self.ElectrodeList.addItem(item)
                self.statusBar().clearMessage()
            except Exception as e:
                print(e)
                self.statusBar().showMessage('Make sure the subject and experiment are inputted correctly', 6000)



    def select_type(self):
        # RETRIEVES TYPE SELECTION FROM LIST
        e_type = self.TypesList.currentItem().text()
        index = self.TypesList.row(self.TypesList.currentItem())
        if index == 0:
            self.base_events_filt = self.base_events  # USE ALL TYPES OF DATA
        else:
            self.base_events_filt = self.base_events[self.base_events.type == e_type]  # FILTERED BY DATA TYPE
        self.NLabel.setText(e_type + ', N = ' + str(np.size(self.base_events_filt)))  # Retrieve number of events for type
        self.EventIndex.setRange(0, np.size(self.base_events_filt) - 1)  # Set counter range to fit number of events
        self.statusBar().clearMessage()
        update_attr(self)  # Update attribute with new data type

    # def select_attr(self):
    #     # RETRIEVES ATTRIBUTE SELECTION FROM LIST
    #     try:
    #         self.attr = self.AttrList.currentItem().text()  # Attribute
    #         self.attr_index = self.AttrList.row(self.AttrList.currentItem())  # Row number of attribute
    #         self.statusBar().clearMessage()
    #         update_attr(self)  # Update attribute based on selected attribute
    #     except Exception as e:
    #         self.statusBar().showMessage(str(e), 6000)

    def select_electrodes(self):
        # RETRIEVES ELECTRODE SELECTION FROM LIST
        items = self.ElectrodeList.selectedItems()  # Selected electrode(s)
        self.electrode_indices = []
        for i in list(items):
            self.electrode_indices.append(self.ElectrodeList.row(i) - 1)
            if -1 in self.electrode_indices:  # USE ALL CHANNELS IF FIRST INDEX IS SELECTED
                if self.mb == 'm':
                    self.mpc = self.monopolar_channels
                elif self.mb == 'b':
                    self.bpc = self.bipolar_pairs
                self.chan_names = self.tagnames
            else:
                if self.mb == 'm':
                    self.mpc = self.monopolar_channels[self.electrode_indices]
                    self.chan_names = self.monopolar_channels[self.electrode_indices]
                elif self.mb == 'b':
                    self.bpc = self.bipolar_pairs[self.electrode_indices]
                    self.chan_names = self.tagnames[self.electrode_indices]
        self.statusBar().showMessage('')


    def get_ind(self):
        # RETRIEVES EVENT INDEX FROM SPINBOX
        self.e_ind = self.EventIndex.value()
        self.statusBar().clearMessage()
        update_attr(self)  # Update attribute display with new index

    def change_session(self):
        # CHANGE THE EEG SESSION TO BE LOADED
        try:
            self.session_no = eval(self.SessionIndex.currentText())
            self.session = self.base_events[self.base_events.session == self.session_no][0][self.eeg_index]  # Update session
            self.EEGLabel.setText(self.session)
        except:
            pass

    def load_eeg(self):
        # LOAD AN ENTIRE SESSION OF EEG DATA
        try:
            self.statusBar().showMessage("LOADING EEG")
            self.plots1 = []  # Will contain the items to plot for the different plot
            self.plots2 = []
            self.plots3 = []
            self.label1 = []
            self.label2 = []
            self.label3 = []
            self.session_no_load = self.session_no
            self.file = 'Notes_session_' + str(self.session_no_load)
            if self.mb == 'm':
                raw_eeg = EEGReader(session_dataroot=self.session, channels=self.mpc)
                self.raw_eeg = raw_eeg.read()
            elif self.mb == 'b':
                channels=[]
                for pair in self.bpc:
                    try:
                        chan1=int(eval(str(pair[0][0:4]).lstrip('0')))
                        channels.append(chan1-1)
                        chan2=int(eval(str(pair[1][0:4]).lstrip('0')))
                        channels.append(chan2-1)
                    except Exception as e:
                        print(e)
                channels = list(set(channels))
                print(channels)
                channels = self.monopolar_channels[channels[:]]
                raw_eeg = EEGReader(session_dataroot=self.session, channels=channels)
                raw_eeg = raw_eeg.read()
                self.raw_eeg = MonopolarToBipolarMapper(time_series=raw_eeg,
                                                     bipolar_pairs=self.bpc).filter()
            self.sample_rate = self.raw_eeg.samplerate
            if self.Downsample_1.isChecked():
                self.ds = self.Downsample.value()
                plot_rate = self.sample_rate / self.ds
            elif self.Downsample_2.isChecked():
                if self.DownsampleList.currentRow() == 0:
                    plot_rate = 250
                    self.ds = round(int(self.sample_rate / plot_rate), 1)
                elif self.DownsampleList.currentRow == 1:
                    plot_rate = 500
                    self.ds = round(int(self.sample_rate / plot_rate), 1)
                elif self.DownsampleList.currentRow == 2:
                    plot_rate = 1000
                    self.ds = round(int(self.sample_rate / plot_rate), 1)
                else:
                    plot_rate = self.sample_rate
                    self.ds = 1
                if self.ds < 1:
                    self.ds = 1
            self.ds = int(self.ds)
            # CLEAR PLOTS AND RESET LEGENDS
            self.plot1.clear()
            self.plot2.clear()
            self.plot3.clear()
            self.leg2.scene().removeItem(self.leg2)
            self.leg2 = self.plot2.addLegend()
            axis1 = pg.AxisItem('top')
            axis1.setGrid(0)
            axis1.linkToView(self.viewbox1)
            #self.plot1.addItem(axis1)
            if self.Bandstop.isChecked():
                b_filter = ButterworthFilter(time_series=self.raw_eeg, freq_range=[58., 62.], filt_type='stop',
                                            order=4)  # Default filter time series to filter out AC noise
                self.bw_eegs = b_filter.filter()
            else:
                self.bw_eegs = self.raw_eeg
            self.bw_eegs.data = self.bw_eegs.data.astype("float32")
            self.numchan = np.size(self.raw_eeg, 0)
            self.RemoveChanList.clear()
            # self.MarkBadList.clear()
            for i in range(self.numchan):
                eeg_to_plot = self.bw_eegs[i]
                # ADD CHANNEL LABELS TO LINES
                name = str(self.chan_names[i])
                self.label3.append(pg.InfiniteLine(pos=(self.numchan - i - 1), angle=0, pen=pg.mkPen('w')))
                label = pg.InfLineLabel(line=self.label3[i], text=str(name), movable=True, position=.05, color='k')
                self.plot3.addItem(self.label3[i])
                self.label1.append(pg.InfiniteLine(pos=eeg_to_plot.values[0, 0], angle=0, pen=pg.mkPen('w')))
                label = pg.InfLineLabel(line=self.label1[i], text=str(name), movable=True, position=.05, color='k')
                self.plot1.addItem(self.label1[i])
                # PLOT
                num_points = np.size(eeg_to_plot.time)
                values = eeg_to_plot.values[0, :][0:num_points - 200]
                time = eeg_to_plot.time[0:num_points - 200]
                chan_average = np.mean(values, 0)
                min = np.min(values - values[0])
                max = np.max(values - values[0])
                # PLOT DOWNSAMPLED INDIVIDUAL CHANNELS
                self.plots1.append(pg.PlotDataItem(time[::self.ds], values[::self.ds], pen=pg.mkPen(color='k')))
                self.plot1.addItem(self.plots1[i])
                # PLOT DOWNSAMPELD INDIVIDUAL CHANNELS CENTERED AROUND 0
                self.plots2.append(pg.PlotDataItem(time[::self.ds], values[::self.ds] - chan_average,
                                              name=self.chan_names[i], pen=pg.mkPen(color=(i, self.numchan), width=1)))
                self.plot2.addItem(self.plots2[i])
                # PLOT DOWNSAMPLED INDIVIDUAL CHANNELS IN ORDER (first on top)
                self.plots3.append(pg.PlotDataItem(time[::self.ds], ((values[::self.ds] - values[0]) /
                    (max - min)) + self.numchan - i - 1, pen=pg.mkPen(color='k')))
                self.plot3.addItem(self.plots3[i])
                # self.names3.append(
                #     pg.TextItem(text=name, color=(0, 0, 0), border=pg.mkPen(color='k', width=1), anchor=(1, 0)))
                # self.names3[i].setPos(0, ((self.numchan - i - 1)))
                # self.plot3.addItem(self.names3[i])
                # self.names1.append(
                #     pg.TextItem(text=name, color=(0, 0, 0), border=pg.mkPen(color='k', width=1), anchor=(1, 1)))
                # self.names1[i].setPos(0, eeg_to_plot.values[0, 0])
                # self.plot1.addItem(self.names1[i])

                item = QListWidgetItem(str(name))
                self.RemoveChanList.addItem(item)
                item = QListWidgetItem(name)
            self.plot1.enableAutoRange()
            self.plot2.enableAutoRange()
            self.plot3.enableAutoRange()
            self.plot1.enableAutoRange()
            self.plot2.enableAutoRange()
            self.plot3.enableAutoRange()
            # self.GainBox.setEnabled(True)
            self.AnnPlotList.setEnabled(True)
            self.AnnPlotButton.setEnabled(True)
            self.FilterButton.setEnabled(True)
            self.RemoveChanButton.setEnabled(True)
            self.MarkBadButton.setEnabled(True)
            self.EventScroll.setEnabled(True)
            self.EventScroll.setRange(0, np.size(self.base_events) - 1)
            self.FilterCenter.setRange(1, round(int(self.sample_rate/2)))
            self.FilterList.clear()
            self.FiltTypes=[]
            self.FiltCutoffs=[]
            self.FiltOrders=[]
            self.LoadPlot.setCurrentIndex(1)
            self.RawRateLabel.setText("Raw rate: " + str(float(self.sample_rate)) + " Hz")
            self.PlottedRateLabel.setText("Plotted rate: " + str(float(plot_rate)) + " Hz")
            self.plot3.setXRange(-1, 20)
            self.plot2.setXRange(-1,20)
            self.plot1.setXRange(-1,20)
            self.plot3.setXRange(-1, 20)
            self.plot2.setXRange(-1, 20)
            self.plot1.setXRange(-1, 20)
            self.statusBar().showMessage('Done', 6000)
        except Exception as e:
            print(e)
            self.statusBar().showMessage(str(e), 6000)

    def run_filter(self):
        # RUN A FILTER ON LOADED EEG DATA
        self.plot1.disableAutoRange()
        self.plot2.disableAutoRange()
        self.plot3.disableAutoRange()
        filter_index = self.FilterBox.currentIndex()
        if filter_index == 0:
            filt_type='high'
        else:
            filt_type = 'low '
        self.FiltTypes.append(filter_index)
        nyquist = self.sample_rate / 2
        cutoff = float(self.FilterCenter.value())
        order = self.FilterOrder.value()
        self.FiltOrders.append(order)
        normal_cutoff = cutoff / nyquist
        self.FiltCutoffs.append(normal_cutoff)
        filt_item = QListWidgetItem(filt_type + ', order: ' + str(order) + ', cutoff: ' + str(cutoff) + ' Hz')
        self.FilterList.addItem(filt_item)
        for i in range(np.size(self.FiltTypes,0)):
            order = self.FiltOrders[i]
            cutoff = self.FiltCutoffs[i]
            if self.FiltTypes[i] == 0:
                btype = 'high'
            else:
                btype = 'low'
            b, a = butter(order, cutoff, btype=btype, analog=False)
            if i == 0:
                filtered = filtfilt(b, a, self.bw_eegs)
            else:
                filtered = filtfilt(b, a, filtered)
        try:
            for i in range(self.numchan):
                eeg_to_plot = filtered[i]
                eeg_to_plot = eeg_to_plot[0,:-200]
                #num_points = np.size(eeg_to_plot, 1)
                #print(num_points)
                chan_average = np.mean(eeg_to_plot)
                min = np.min(eeg_to_plot[50:] - eeg_to_plot[50])
                max = np.max(eeg_to_plot[50:] - eeg_to_plot[50])
                self.plots1[i].setData(self.plots1[i].xData[:],
                                  eeg_to_plot[::self.ds],
                                  pen=pg.mkPen(color='k'))
                self.label1[i].setValue(eeg_to_plot[0])

                self.plots2[i].setData(self.plots2[i].xData[:],
                                  eeg_to_plot[::self.ds] - chan_average,
                                  name=self.chan_names[i], pen=pg.mkPen(color=(i, self.numchan), width=1))
                self.plots3[i].setData(self.plots3[i].xData[:], (
                    (eeg_to_plot[::self.ds] - eeg_to_plot[0]) / (
                        max - min) + self.numchan - i - 1), pen=pg.mkPen(color='k'))
                self.label1[i].setValue(self.numchan - i - 1)
                #self.names1[i].setPos(0, eeg_to_plot[50])
            self.RemoveAllButton.setEnabled(True)
            self.RemoveButton.setEnabled(True)
            # self.FilterButton.setEnabled(False)
            self.LoadPlot.setCurrentIndex(1)
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def unapply_filter(self):
        try:
            for SelectedItem in self.FilterList.selectedItems():
                index = self.FilterList.row(SelectedItem)
                self.FilterList.takeItem(index)
            self.FiltOrders.pop(index)
            self.FiltTypes.pop(index)
            self.FiltCutoffs.pop(index)
            for i in range(np.size(self.FiltTypes,0)):
                order = self.FiltOrders[i]
                cutoff = self.FiltCutoffs[i]
                if self.FiltTypes[i] == 0:
                    btype = 'high'
                else:
                    btype = 'low'
                b, a = butter(order, cutoff, btype=btype, analog=False)
                if i == 0:
                    filtered = filtfilt(b, a, self.bw_eegs)
                else:
                    filtered = filtfilt(b, a, filtered)
            if np.size(self.FiltOrders) == 0:
                filtered = self.bw_eegs
        except Exception as e:
            print(e)
        try:
            for i in range(self.numchan):
                eeg_to_plot = filtered[i]
                eeg_to_plot = eeg_to_plot[0,:-200]
                #num_points = np.size(eeg_to_plot, 1)
                #print(num_points)
                chan_average = np.mean(eeg_to_plot)
                min = np.min(eeg_to_plot[50:] - eeg_to_plot[50])
                max = np.max(eeg_to_plot[50:] - eeg_to_plot[50])
                self.plots1[i].setData(self.plots1[i].xData[:],
                                  eeg_to_plot[::self.ds],
                                  pen=pg.mkPen(color='k'))
                self.label1[i].setValue(eeg_to_plot[0])

                self.plots2[i].setData(self.plots2[i].xData[:],
                                  eeg_to_plot[::self.ds] - chan_average,
                                  name=self.chan_names[i], pen=pg.mkPen(color=(i, self.numchan), width=1))
                self.plots3[i].setData(self.plots3[i].xData[:], (
                    (eeg_to_plot[::self.ds] - eeg_to_plot[0]) / (
                        max - min) + self.numchan - i - 1), pen=pg.mkPen(color='k'))
                self.label1[i].setValue(self.numchan - i - 1)
                #self.names1[i].setPos(0, eeg_to_plot[50])
            self.RemoveAllButton.setEnabled(True)
            self.RemoveButton.setEnabled(True)
            # self.FilterButton.setEnabled(False)
            self.LoadPlot.setCurrentIndex(1)
        except Exception as e:
            print(e)
        # itemsTextList = [str(self.FilterList.item(i).text()) for i in range(self.FilterList.count())]
        # nyquist = self.sample_rate / 2
        # for filter in itemsTextList:
        #     if filter[0] == 'l':
        #         filttype = 'low'
        #     else:
        #         filttype = 'high'
        #     order = eval(filter[18])
        #     decimal_index = filter.find('.')
        #     cutoff = filter[29:decimal_index]
        #     normal_cutoff = cutoff / nyquist
        #     b, a = butter(order, normal_cutoff, btype=filttype, analog=False)
        pass

    def remove_filter(self):
        # REMOVE APPLIED FILTERs
        self.plot1.disableAutoRange()
        self.plot2.disableAutoRange()
        self.plot3.disableAutoRange()
        for i in range(self.numchan):
            eeg_to_plot = self.bw_eegs[i]
            num_points = np.size(eeg_to_plot.time)
            values = eeg_to_plot.values[0, :][0:num_points - 200]
            time = eeg_to_plot.time[0:num_points - 200]
            chan_average = np.mean(values, 0)
            min = np.min(values - values[0])
            max = np.max(values - values[0])
            self.plots1[i].setData(time[::self.ds], values[::self.ds], pen=pg.mkPen(color='k'))
            self.label1[i].setValue(values[0])
            self.plots2[i].setData(time[::self.ds], values[::self.ds] - chan_average,
                                               name=self.chan_names[i], pen=pg.mkPen(color=(i, self.numchan), width=1))
            self.plots3[i].setData(time[::self.ds], ((values[::self.ds] - values[0]) /
                                                                 (max - min)) + self.numchan - i - 1,
                                               pen=pg.mkPen(color='k'))
            self.label3[i].setValue(self.numchan - i - 1)
            #self.names1[i].setPos(0, eeg_to_plot.values[0, 0])
        self.RemoveAllButton.setEnabled(False)
        self.RemoveButton.setEnabled(False)
        self.plot1.disableAutoRange()
        self.plot2.disableAutoRange()
        self.plot3.disableAutoRange()
        self.FilterList.clear()

    # def change_gain(self):
    #     # CHANGE THE GAIN OF THE GRAPH
    #      bw_eeg, chan_average, chan_names, numchan, base_eegs, leg2
    #     for i in range(numchan):
    #         eeg_to_plot = bw_eegs[i]
    #         num_points = np.size(eeg_to_plot.time)
    #         chan_average = np.mean(eeg_to_plot.values[0, :], 0)
    #         min = np.min(eeg_to_plot.values[0, :][0:num_points - 200] - eeg_to_plot.values[0, 0])
    #         max = np.max(eeg_to_plot.values[0, :][0:num_points - 200] - eeg_to_plot.values[0, 0])
    #         try:
    #             plots1[i].setData(plots1[i].xData, plots1[i].yData * self.GainBox.value())
    #             plots2[i].setData(plots2[i].xData, plots2[i].yData * self.GainBox.value())
    #             plots3[i].setData(plots3[i].xData, plots3[i].yData * self.GainBox.value())
    #         except Exception as e:
    #             print(e)

    def toggle_horizontal(self):
        # ENABLE HORIZONTAL SCALING / SCROLLING
        if self.HorizontalBox.isChecked():
            self.plot1.setMouseEnabled(x=True)
            self.plot2.setMouseEnabled(x=True)
            self.plot3.setMouseEnabled(x=True)
        else:
            self.plot1.setMouseEnabled(x=False)
            self.plot2.setMouseEnabled(x=False)
            self.plot3.setMouseEnabled(x=False)

    def iso_horizontal(self):
        # ISOLATE HORIZONTAL SCALING / SCROLLING
        self.plot1.setMouseEnabled(x=True)
        self.plot2.setMouseEnabled(x=True)
        self.plot3.setMouseEnabled(x=True)
        self.plot1.setMouseEnabled(y=False)
        self.plot2.setMouseEnabled(y=False)
        self.plot3.setMouseEnabled(y=False)
        self.VerticalBox.setCheckState(False)
        self.HorizontalBox.setCheckState(True)

    def toggle_vertical(self):
        # ENABLE VERTICAL SCALING / SCROLLING
        if self.VerticalBox.isChecked():
            self.plot1.setMouseEnabled(y=True)
            self.plot2.setMouseEnabled(y=True)
            self.plot3.setMouseEnabled(y=True)
        else:
            self.plot1.setMouseEnabled(y=False)
            self.plot2.setMouseEnabled(y=False)
            self.plot3.setMouseEnabled(y=False)

    def iso_vertical(self):
        # ISOLATE VERTICAL SCALING / SCROLLING
        self.plot1.setMouseEnabled(y=True)
        self.plot2.setMouseEnabled(y=True)
        self.plot3.setMouseEnabled(y=True)
        self.plot1.setMouseEnabled(x=False)
        self.plot2.setMouseEnabled(x=False)
        self.plot3.setMouseEnabled(x=False)
        self.VerticalBox.setCheckState(True)
        self.HorizontalBox.setCheckState(False)

    def zoom_both(self):
        self.plot1.setMouseEnabled(y=True)
        self.plot2.setMouseEnabled(y=True)
        self.plot3.setMouseEnabled(y=True)
        self.plot1.setMouseEnabled(x=True)
        self.plot2.setMouseEnabled(x=True)
        self.plot3.setMouseEnabled(x=True)
        self.VerticalBox.setCheckState(True)
        self.HorizontalBox.setCheckState(True)

    def box_zoom(self):
        if self.BoxZoomBox.isChecked():
            self.viewbox1.setMouseMode(self.viewbox1.RectMode)
            self.viewbox2.setMouseMode(self.viewbox2.RectMode)
            self.viewbox3.setMouseMode(self.viewbox3.RectMode)
        else:
            self.viewbox1.setMouseMode(self.viewbox1.PanMode)
            self.viewbox2.setMouseMode(self.viewbox2.PanMode)
            self.viewbox3.setMouseMode(self.viewbox3.PanMode)

    def box_hotkey(self):
        if self.BoxZoomBox.isChecked():
            self.viewbox1.setMouseMode(self.viewbox1.PanMode)
            self.viewbox2.setMouseMode(self.viewbox2.PanMode)
            self.viewbox3.setMouseMode(self.viewbox3.PanMode)
            self.BoxZoomBox.setCheckState(False)
        else:
            self.viewbox1.setMouseMode(self.viewbox1.RectMode)
            self.viewbox2.setMouseMode(self.viewbox2.RectMode)
            self.viewbox3.setMouseMode(self.viewbox3.RectMode)
            self.BoxZoomBox.setCheckState(True)

    def reset_view(self):
        # AUTOSCALE AXES TO FIT ALL THE DATA
        self.plot1.enableAutoRange()
        self.plot2.enableAutoRange()
        self.plot3.enableAutoRange()
        self.plot1.disableAutoRange()
        self.plot2.disableAutoRange()
        self.plot3.disableAutoRange()

    def undo_zoom(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            self.viewbox1 = self.plot1.getself.viewbox()
            self.viewbox1.scaleHistory(-1)
        if current_tab == 2:
            self.viewbox2 = self.plot2.getself.viewbox()
            self.viewbox2.scaleHistory(-1)
        if current_tab == 0:
            self.viewbox3 = self.plot3.getself.viewbox()
            self.viewbox3.scaleHistory(-1)

    def select_annotations(self):
        items = self.AnnPlotList.selectedItems()  # Selected annotation(s)
        self.filtered_events = []
        try:
            self.annots = []
            for i in list(items):
                self.annots.append(str(i.text()))
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def view_annotations(self):
        # UPDATE ANNOTATION LINES AND TEXT
        try:
            line_count = 0  # Counter for loop
            text_count = 0  # Counter for text
            sess_data = self.base_events[self.base_events.session == self.session_no_load]
            current_tab = self.PlotTabs.currentIndex()
            if current_tab == 1:
                current_plot = self.plot1
                try:
                    for line in self.self.lines:
                        current_plot.removeItem(line)
                except:
                    pass
                self.lines = []
                for annot in self.annots:
                    data = sess_data[sess_data.type == annot]
                    for datum in data:
                        offset = datum[self.offset_index]
                        type = datum[self.type_index]
                        self.lines.append(pg.InfiniteLine(pos=offset / self.sample_rate, angle=90,
                                                     pen=pg.mkPen(color=(text_count, np.size(self.annots)), width=5)))
                        label = pg.InfLineLabel(line=self.lines[line_count], text=annot, movable=True, position=.95, color='k')
                        current_plot.addItem(self.lines[line_count])
                        line_count += 1
                    text_count += 1
            elif current_tab == 2:
                current_plot = self.plot2
                try:
                    for line in self.lines2:
                        current_plot.removeItem(line)
                except:
                    pass
                self.lines2 = []
                for annot in self.annots:
                    data = sess_data[sess_data.type == annot]
                    for datum in data:
                        offset = datum[self.offset_index]
                        type = datum[self.type_index]
                        self.lines2.append(pg.InfiniteLine(pos=offset / self.sample_rate, angle=90,
                                                      pen=pg.mkPen(color='k', width=5)))
                        label = pg.InfLineLabel(line=self.lines2[line_count], text=annot, movable=True, position=.95, color='k')
                        current_plot.addItem(self.lines2[line_count])
                        line_count += 1
                    text_count += 1
            else:
                current_plot = self.plot3
                try:
                    for line in self.lines3:
                        current_plot.removeItem(line)
                except:
                    pass
                self.lines3 = []
                for annot in self.annots:
                    data = sess_data[sess_data.type == annot]
                    for datum in data:
                        offset = datum[self.offset_index]
                        type = datum[self.type_index]
                        self.lines3.append(pg.InfiniteLine(pos=offset / self.sample_rate, angle=90,
                                                      pen=pg.mkPen(color=(text_count, np.size(self.annots)), width=5)))
                        label = pg.InfLineLabel(line=self.lines3[line_count], text=annot, movable=True, position=.95, color='k')
                        current_plot.addItem(self.lines3[line_count])
                        line_count += 1
                    text_count += 1
            self.statusBar().showMessage('')
            self.ClearAnnButton.setEnabled(True)
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def clear_annotations(self):
        current_tab = self.PlotTabs.currentIndex()
        try:
            if current_tab == 1:
                current_plot = self.plot1
                for line in self.lines:
                    current_plot.removeItem(line)
                self.lines = []
            elif current_tab == 2:
                current_plot = self.plot2
                for line in self.lines2:
                    current_plot.removeItem(line)
                for text in self.texts2:
                    current_plot.removeItem(text)
                self.lines2 = []
                self.texts2 = []
            else:
                current_plot = self.plot3
                for line in self.lines3:
                    current_plot.removeItem(line)
                self.lines3 = []
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def remove_channels(self):
        chans = []
        channels_to_remove = self.RemoveChanList.selectedItems()
        count = 0
        self.plot1.disableAutoRange()
        self.plot2.disableAutoRange()
        self.plot3.disableAutoRange()
        for chan in channels_to_remove:
            chans.append(self.RemoveChanList.row(chan))
            try:
                if self.plots1[chans[count]].isVisible():
                    self.plots1[chans[count]].setVisible(False)
                    self.label1[chans[count]].setVisible(False)
                else:
                    self.plots1[chans[count]].setVisible(True)
                    self.label1[chans[count]].setVisible(True)
                if self.plots2[chans[count]].isVisible():
                    self.plots2[chans[count]].setVisible(False)
                else:
                    self.plots2[chans[count]].setVisible(True)
                if self.plots3[chans[count]].isVisible():
                    self.plots3[chans[count]].setVisible(False)
                    self.label3[chans[count]].setVisible(False)
                else:
                    self.plots3[chans[count]].setVisible(True)
                    self.label3[chans[count]].setVisible(True)
                count += 1
                self.plot1.disableAutoRange()
                self.plot2.disableAutoRange()
                self.plot3.disableAutoRange()
            except Exception as e:
                self.statusBar().showMessage(str(e), 6000)

    def mark_bad(self):
        try:
            self.text_name = self.directory + self.file + '.txt'
            self.f = open(self.text_name, "a+")
            text = str(self.MessageBox.toPlainText())
            self.f.write("\r\n" + text + "\r\n")
        except Exception as e:
             self.statusBar().showMessage(str(e), 6000)

    def mark_default(self):
        try:
            self.directory = self.eeg[0:self.directory_index + 6]
            self.file = 'Notes_session_' + str(self.session_no_load)
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def name_change(self):
        self.file = str(self.TextName.text())
        pass

    def path_change(self):
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select folder to save text in")) + '/'
        print(self.directory)
        pass

    def mark_event(self):
        try:
            self.text_name = self.directory + self.file + '.txt'
            self.f = open(self.text_name, "a+")
            time_stamp = self.lower_bound
            text = ("(" + str(time_stamp) + "seconds), Event number " + str(self.session_index) + " (" +  str((self.EventScrollBox.currentText())) + ") is bad")
            self.f.write("\r\n" + text + "\r\n")
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def tab1(self):
        self.PlotTabs.setCurrentIndex(0)

    def tab2(self):
        self.PlotTabs.setCurrentIndex(1)

    def tab3(self):
        self.PlotTabs.setCurrentIndex(2)

    def plottab(self):
        self.LoadPlot.setCurrentIndex(1)

    def loadtab(self):
        self.LoadPlot.setCurrentIndex(0)

    def pan_left(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        range = x_axes[1] - x_axes[0]
        increment = range / 10
        current_plot.setXRange(x_axes[0] - increment, x_axes[1] - increment, padding=0)

    def page_left(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        range = x_axes[1] - x_axes[0]
        current_plot.setXRange(x_axes[0] - range, x_axes[1] - range, padding=0)

    def pan_right(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        range = x_axes[1] - x_axes[0]
        increment = range / 10
        current_plot.setXRange(x_axes[0] + increment, x_axes[1] + increment, padding=0)

    def page_right(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        range = x_axes[1] - x_axes[0]
        current_plot.setXRange(x_axes[0] + range, x_axes[1] + range, padding=0)

    def pan_up(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        y_axes = current_plot.viewRange()[1]
        range = y_axes[1] - y_axes[0]
        increment = range / 10
        current_plot.setYRange(y_axes[0] + increment, y_axes[1] + increment, padding=0)

    def page_up(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        y_axes = current_plot.viewRange()[1]
        range = y_axes[1] - y_axes[0]
        current_plot.setYRange(y_axes[0] + range, y_axes[1] + range, padding=0)

    def change_window(self):
        try:
            self.win_len = float(eval(self.WindowLength.text())) / 1000
            current_tab = self.PlotTabs.currentIndex()
            if current_tab == 1:
                current_plot = self.plot1
            elif current_tab == 2:
                current_plot = self.plot2
            elif current_tab == 0:
                current_plot = self.plot3
            x_axes = current_plot.viewRange()[0]
            current_plot.setXRange(x_axes[0], x_axes[0] + self.win_len, padding=0)
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def time_scroll(self):
        try:
            self.win_len = float(eval(self.WindowLength.text())) / 1000
            self.new_time = float(eval(self.TimeScroll.text()))
            current_tab = self.PlotTabs.currentIndex()
            if current_tab == 1:
                current_plot = self.plot1
            elif current_tab == 2:
                current_plot = self.plot2
            elif current_tab == 0:
                current_plot = self.plot3
            current_plot.setXRange(self.new_time, self.new_time + self.win_len, padding=0)
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)

    def filter_event_scroll(self):
        try:
            type = str((self.EventScrollBox.currentText()))
            if self.EventScrollBox.currentIndex() == 0:
                filtered_events_total = self.base_events
            else:
                filtered_events_total = self.base_events[self.base_events.type == type]
            filtered_events = filtered_events_total[filtered_events_total.session == self.session_no_load]
            self.EventScroll.setRange(0, np.size(filtered_events) - 1)
            offset = filtered_events[self.EventScroll.value()][self.offset_index]
            self.lower_bound = filtered_events[self.EventScroll.value()][self.offset_index]/float(self.sample_rate)
            session_offsets = self.base_events[self.base_events.session == self.session_no_load].eegoffset
            self.session_index = np.where(session_offsets == offset)[0][0]
            current_tab = self.PlotTabs.currentIndex()
            if current_tab == 1:
                current_plot = self.plot1
            elif current_tab == 2:
                current_plot = self.plot2
            elif current_tab == 0:
                current_plot = self.plot3
            win_len = float(eval(self.WindowLength.text())) / 1000
            current_plot.setXRange(self.lower_bound, self.lower_bound + win_len, padding=0)
            self.EventType.setText("Event type: " + str(filtered_events[self.EventScroll.value()][self.type_index]))
        except Exception as e:
            self.statusBar().showMessage(str(e), 6000)
            pass

    def event_scroll_up(self):
        self.EventScroll.setValue(self.EventScroll.value() + 1)

    def event_scroll_down(self):
        self.EventScroll.setValue(self.EventScroll.value() - 1)

    def pan_down(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        y_axes = current_plot.viewRange()[1]
        range = y_axes[1] - y_axes[0]
        increment = range / 10
        current_plot.setYRange(y_axes[0] - increment, y_axes[1] - increment, padding=0)

    def page_down(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        y_axes = current_plot.viewRange()[1]
        range = y_axes[1] - y_axes[0]
        current_plot.setYRange(y_axes[0] - range, y_axes[1] - range, padding=0)

    def zoom_in(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        y_axes = current_plot.viewRange()[1]
        x_range = x_axes[1] - x_axes[0]
        y_range = y_axes[1] - y_axes[0]
        x_increment = x_range / 10
        y_increment = y_range / 10
        current_plot.setYRange(y_axes[0] + y_increment, y_axes[1] - y_increment, padding=0)
        current_plot.setXRange(x_axes[0] + x_increment, x_axes[1] - x_increment, padding=0)

    def zoom_out(self):
        current_tab = self.PlotTabs.currentIndex()
        if current_tab == 1:
            current_plot = self.plot1
        elif current_tab == 2:
            current_plot = self.plot2
        elif current_tab == 0:
            current_plot = self.plot3
        x_axes = current_plot.viewRange()[0]
        y_axes = current_plot.viewRange()[1]
        x_range = x_axes[1] - x_axes[0]
        y_range = y_axes[1] - y_axes[0]
        x_increment = x_range / 10
        y_increment = y_range / 10
        current_plot.setYRange(y_axes[0] - y_increment, y_axes[1] + y_increment, padding=0)
        current_plot.setXRange(x_axes[0] - x_increment, x_axes[1] + x_increment, padding=0)


def update_attr(obj):
    # UPDATE ATTRIBUTE DISPLAY TEXT
    try:
        obj.AttrList.clear()  # Clear list and populate it with attributes
        for count in range(np.size(obj.attributes)):
            string = (str(obj.base_events_filt[obj.e_ind][count]))  # Update attribute display
            item = QListWidgetItem(obj.attributes[count] + ': ' + string)
            obj.AttrList.addItem(item)
    except Exception as e:
        print(e)


def power_decomp(eeg, buf):
    # SPECTRAL DECOMPOSITION
    global buffer
    resample = -1
    frequencies = np.linspace(1, 60, num=5)
    width = 6
    print('Starting power decomposition.')
    print(eeg)
    power, phase = MorletWaveletFilter(time_series=eeg, freqs=frequencies, width=6, output='power').filter()
    print('here')
    if buf != 0:
        power = power.remove_buffer(duration=buf)
    try:
        power = power.transpose('events', 'channels', 'frequency', 'time')
    except:
        try:
            power = power.transpose('events', 'bipolar_pairs', 'frequency', 'time')
        except:
            raise ValueError('Check the structure of the power. Doesnt seem to have bp or mp')
    if resample != -1:
        print('resampling')
        power = ResampleFilter(time_series=power, resamplerate=resample).filter()
    return power


if __name__ == '__main__':  # Part of PyQt GUI skeleton, DO NOT ALTER
    app = QApplication(sys.argv)
    # noinspection PyUnresolvedReferences
    app.aboutToQuit.connect(app.deleteLater)  # if using IPython Console
    window = Ui()
    sys.exit(app.exec_())
