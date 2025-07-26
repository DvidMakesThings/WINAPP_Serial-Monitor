import re
import json
import csv
import threading
from datetime import datetime
from collections import deque
import numpy as np

class DataProcessor:
    def __init__(self, max_buffer_size=10000):
        self.max_buffer_size = max_buffer_size
        self.raw_buffer = deque(maxlen=max_buffer_size)
        
        # Separate buffers for different data types
        self.data_buffer = deque(maxlen=max_buffer_size)  # [DATA] entries
        self.plot_buffer = deque(maxlen=max_buffer_size)  # [PLOT] entries  
        self.meas_buffer = deque(maxlen=max_buffer_size)  # [MEAS] entries
        
        self.filtered_buffer = deque(maxlen=max_buffer_size)
        self.lock = threading.Lock()
        
        # Filtering
        self.filter_enabled = False
        self.filter_pattern = ""
        self.filter_regex = None
        
        # Structured data parsing patterns
        self.structured_patterns = {
            'DATA': re.compile(r'\[DATA\]\s*([^:]+):\s*([-+]?\d*\.?\d+)'),
            'PLOT': re.compile(r'\[PLOT\]\s*([^:]+):\s*([-+]?\d*\.?\d+)'),
            'MEAS': re.compile(r'\[MEAS\]\s*([^:]+):\s*([-+]?\d*\.?\d+)')
        }
        
        # Callbacks for real-time updates
        self.data_callbacks = []
        self.plot_callbacks = []
        self.structured_callbacks = []  # For structured data updates
    
    def add_data_callback(self, callback):
        """Add callback for when new data arrives"""
        self.data_callbacks.append(callback)
    
    def add_plot_callback(self, callback):
        """Add callback for when new numeric data arrives"""
        self.plot_callbacks.append(callback)
    
    def add_structured_callback(self, callback):
        """Add callback for structured data (DATA/PLOT/MEAS)"""
        self.structured_callbacks.append(callback)
    
    def process_data(self, data, timestamp=None):
        """Process incoming serial data"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            # Store raw data with timestamp
            entry = {
                'timestamp': timestamp,
                'data': data,
                'raw': data.strip()
            }
            self.raw_buffer.append(entry)
            
            # Apply filtering if enabled
            if self.filter_enabled and self.filter_regex:
                if not self.filter_regex.search(data):
                    return  # Skip this data
            
            self.filtered_buffer.append(entry)
            
            # Extract structured data
            structured_data = self.extract_structured_data(data, timestamp)
            if structured_data:
                for data_type, name, value in structured_data:
                    entry = {
                        'timestamp': timestamp,
                        'type': data_type,
                        'name': name,
                        'value': value,
                        'raw_data': data.strip()
                    }
                    
                    # Store in appropriate buffer
                    if data_type == 'DATA':
                        self.data_buffer.append(entry)
                    elif data_type == 'PLOT':
                        self.plot_buffer.append(entry)
                        # Notify plot callbacks for PLOT data
                        for callback in self.plot_callbacks:
                            try:
                                callback(timestamp, value, name)
                            except Exception as e:
                                print(f"Plot callback error: {e}")
                    elif data_type == 'MEAS':
                        self.meas_buffer.append(entry)
                    
                    # Notify structured data callbacks
                    for callback in self.structured_callbacks:
                        try:
                            callback(data_type, name, value, timestamp)
                        except Exception as e:
                            print(f"Structured callback error: {e}")
            
            # Notify data callbacks
            for callback in self.data_callbacks:
                try:
                    callback(entry)
                except Exception as e:
                    print(f"Data callback error: {e}")
    
    def extract_structured_data(self, data, timestamp):
        """Extract structured data from [DATA]/[PLOT]/[MEAS] tags"""
        results = []
        
        for data_type, pattern in self.structured_patterns.items():
            matches = pattern.findall(data)
            for name, value_str in matches:
                try:
                    value = float(value_str)
                    results.append((data_type, name.strip(), value))
                except ValueError:
                    continue
        
        return results
    
    def set_filter(self, pattern, enabled=True):
        """Set data filter pattern"""
        self.filter_enabled = enabled
        self.filter_pattern = pattern
        if pattern and enabled:
            try:
                self.filter_regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                self.filter_regex = None
                return False
        else:
            self.filter_regex = None
        return True
    
    def get_recent_data(self, count=100):
        """Get recent filtered data entries"""
        with self.lock:
            return list(self.filtered_buffer)[-count:]
    
    def get_recent_structured_data(self, data_type=None, count=100):
        """Get recent structured data for plotting"""
        with self.lock:
            if data_type == 'DATA':
                return list(self.data_buffer)[-count:]
            elif data_type == 'PLOT':
                return list(self.plot_buffer)[-count:]
            elif data_type == 'MEAS':
                return list(self.meas_buffer)[-count:]
            else:
                # Return all structured data
                all_data = list(self.data_buffer) + list(self.plot_buffer) + list(self.meas_buffer)
                return sorted(all_data, key=lambda x: x['timestamp'])[-count:]
    
    def get_data_by_name(self, name, data_type=None, count=100):
        """Get data for a specific measurement name"""
        with self.lock:
            buffers = []
            if data_type == 'DATA' or data_type is None:
                buffers.extend(self.data_buffer)
            if data_type == 'PLOT' or data_type is None:
                buffers.extend(self.plot_buffer)
            if data_type == 'MEAS' or data_type is None:
                buffers.extend(self.meas_buffer)
            
            filtered = [entry for entry in buffers if entry['name'] == name]
            return sorted(filtered, key=lambda x: x['timestamp'])[-count:]
    
    def get_available_names(self, data_type=None):
        """Get list of available measurement names"""
        with self.lock:
            names = set()
            buffers = []
            if data_type == 'DATA' or data_type is None:
                buffers.extend(self.data_buffer)
            if data_type == 'PLOT' or data_type is None:
                buffers.extend(self.plot_buffer)
            if data_type == 'MEAS' or data_type is None:
                buffers.extend(self.meas_buffer)
            
            for entry in buffers:
                names.add(entry['name'])
            
            return sorted(list(names))
    
    def export_data(self, filename, format_type='csv', data_type='filtered'):
        """Export data to file in various formats"""
        with self.lock:
            if data_type == 'raw':
                data = list(self.raw_buffer)
            elif data_type == 'structured':
                data = list(self.data_buffer) + list(self.plot_buffer) + list(self.meas_buffer)
                data = sorted(data, key=lambda x: x['timestamp'])
            elif data_type == 'plot':
                data = list(self.plot_buffer)
            elif data_type == 'data':
                data = list(self.data_buffer)
            elif data_type == 'meas':
                data = list(self.meas_buffer)
            else:
                data = list(self.filtered_buffer)
        
        if format_type.lower() == 'csv':
            self._export_csv(filename, data, data_type)
        elif format_type.lower() == 'json':
            self._export_json(filename, data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_csv(self, filename, data, data_type):
        """Export data to CSV format"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data_type in ['structured', 'plot', 'data', 'meas']:
                fieldnames = ['timestamp', 'type', 'name', 'value', 'raw_data']
            else:
                fieldnames = ['timestamp', 'data']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in data:
                row = {'timestamp': entry['timestamp'].isoformat()}
                if data_type in ['structured', 'plot', 'data', 'meas']:
                    row.update({
                        'type': entry.get('type', ''),
                        'name': entry.get('name', ''),
                        'value': entry['value'],
                        'raw_data': entry['raw_data']
                    })
                else:
                    row['data'] = entry['data']
                writer.writerow(row)
    
    def _export_json(self, filename, data):
        """Export data to JSON format"""
        json_data = []
        for entry in data:
            json_entry = entry.copy()
            json_entry['timestamp'] = entry['timestamp'].isoformat()
            json_data.append(json_entry)
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
    
    def clear_buffers(self):
        """Clear all data buffers"""
        with self.lock:
            self.raw_buffer.clear()
            self.data_buffer.clear()
            self.plot_buffer.clear()
            self.meas_buffer.clear()
            self.filtered_buffer.clear()
    
    def get_statistics(self):
        """Get basic statistics about the data"""
        with self.lock:
            stats = {
                'total_entries': len(self.raw_buffer),
                'filtered_entries': len(self.filtered_buffer),
                'data_entries': len(self.data_buffer),
                'plot_entries': len(self.plot_buffer),
                'meas_entries': len(self.meas_buffer),
                'filter_enabled': self.filter_enabled,
                'filter_pattern': self.filter_pattern
            }
            
            # Statistics for PLOT data (most relevant for plotting)
            if self.plot_buffer:
                values = [entry['value'] for entry in self.plot_buffer]
                stats.update({
                    'plot_min': min(values),
                    'plot_max': max(values),
                    'plot_avg': sum(values) / len(values),
                    'plot_std': np.std(values) if len(values) > 1 else 0
                })
            
            return stats