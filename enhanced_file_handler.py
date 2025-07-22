import os
import json
import csv
from datetime import datetime
from tkinter import filedialog, messagebox
import pandas as pd

class EnhancedFileHandler:
    def __init__(self):
        self.supported_formats = {
            'txt': 'Text File',
            'csv': 'CSV File', 
            'json': 'JSON File',
            'xlsx': 'Excel File',
            'log': 'Log File'
        }
    
    def save_log(self, log_text, filename=None, format_type='txt', include_timestamp=True):
        """
        Enhanced save log with multiple format support and timestamping
        """
        if not filename:
            filetypes = [(desc, f"*.{ext}") for ext, desc in self.supported_formats.items()]
            filename = filedialog.asksaveasfilename(
                title="Save Log",
                filetypes=filetypes,
                defaultextension=".txt"
            )
        
        if not filename:
            return False
        
        try:
            # Determine format from extension if not specified
            if format_type == 'auto':
                ext = os.path.splitext(filename)[1].lower().lstrip('.')
                format_type = ext if ext in self.supported_formats else 'txt'
            
            # Add timestamp header if requested
            if include_timestamp:
                timestamp_header = f"# Log saved on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                timestamp_header += f"# Format: {format_type.upper()}\n"
                timestamp_header += "# " + "="*50 + "\n\n"
            else:
                timestamp_header = ""
            
            if format_type == 'txt' or format_type == 'log':
                self._save_text(filename, timestamp_header + log_text)
            elif format_type == 'csv':
                self._save_csv(filename, log_text, timestamp_header)
            elif format_type == 'json':
                self._save_json(filename, log_text, timestamp_header)
            elif format_type == 'xlsx':
                self._save_excel(filename, log_text, timestamp_header)
            else:
                # Default to text
                self._save_text(filename, timestamp_header + log_text)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
            return False
    
    def _save_text(self, filename, content):
        """Save as plain text file"""
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
    
    def _save_csv(self, filename, log_text, header=""):
        """Save as CSV file with parsed data"""
        lines = log_text.strip().split('\n')
        
        # Try to parse structured data
        csv_data = []
        for i, line in enumerate(lines):
            if line.strip():
                # Basic parsing - can be enhanced based on data format
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                csv_data.append({
                    'Line': i + 1,
                    'Timestamp': timestamp,
                    'Data': line.strip()
                })
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if header:
                csvfile.write(f"# {header}\n")
            
            if csv_data:
                fieldnames = ['Line', 'Timestamp', 'Data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            else:
                csvfile.write("No data to export\n")
    
    def _save_json(self, filename, log_text, header=""):
        """Save as JSON file"""
        lines = log_text.strip().split('\n')
        
        json_data = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'format': 'json',
                'total_lines': len([l for l in lines if l.strip()])
            },
            'data': []
        }
        
        if header:
            json_data['metadata']['header'] = header.strip()
        
        for i, line in enumerate(lines):
            if line.strip():
                json_data['data'].append({
                    'line_number': i + 1,
                    'timestamp': datetime.now().isoformat(),
                    'content': line.strip()
                })
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
    
    def _save_excel(self, filename, log_text, header=""):
        """Save as Excel file"""
        lines = log_text.strip().split('\n')
        
        # Prepare data for DataFrame
        data = []
        for i, line in enumerate(lines):
            if line.strip():
                data.append({
                    'Line': i + 1,
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Data': line.strip(),
                    'Length': len(line.strip())
                })
        
        if data:
            df = pd.DataFrame(data)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Serial_Data', index=False)
                
                # Summary sheet
                summary_data = {
                    'Metric': ['Total Lines', 'Export Time', 'Average Line Length', 'Max Line Length'],
                    'Value': [
                        len(data),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        f"{df['Length'].mean():.1f}" if len(data) > 0 else "0",
                        df['Length'].max() if len(data) > 0 else 0
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        else:
            # Create empty Excel file
            df = pd.DataFrame({'Message': ['No data to export']})
            df.to_excel(filename, index=False)
    
    def load_log(self, filename=None):
        """Load a previously saved log file"""
        if not filename:
            filetypes = [(desc, f"*.{ext}") for ext, desc in self.supported_formats.items()]
            filename = filedialog.askopenfilename(
                title="Load Log",
                filetypes=filetypes
            )
        
        if not filename:
            return None
        
        try:
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            
            if ext in ['txt', 'log']:
                return self._load_text(filename)
            elif ext == 'csv':
                return self._load_csv(filename)
            elif ext == 'json':
                return self._load_json(filename)
            elif ext in ['xlsx', 'xls']:
                return self._load_excel(filename)
            else:
                # Try as text
                return self._load_text(filename)
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load file: {str(e)}")
            return None
    
    def _load_text(self, filename):
        """Load text file"""
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _load_csv(self, filename):
        """Load CSV file and convert back to text"""
        df = pd.read_csv(filename)
        if 'Data' in df.columns:
            return '\n'.join(df['Data'].astype(str))
        else:
            return df.to_string()
    
    def _load_json(self, filename):
        """Load JSON file and convert back to text"""
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if 'data' in data and isinstance(data['data'], list):
            lines = []
            for entry in data['data']:
                if isinstance(entry, dict) and 'content' in entry:
                    lines.append(entry['content'])
                else:
                    lines.append(str(entry))
            return '\n'.join(lines)
        else:
            return json.dumps(data, indent=2)
    
    def _load_excel(self, filename):
        """Load Excel file and convert back to text"""
        df = pd.read_excel(filename, sheet_name=0)  # Load first sheet
        if 'Data' in df.columns:
            return '\n'.join(df['Data'].astype(str))
        else:
            return df.to_string()
    
    def export_data_advanced(self, data_processor, filename=None, format_type='csv', 
                           data_type='filtered', include_metadata=True):
        """
        Advanced export using DataProcessor
        """
        if not filename:
            ext = format_type.lower()
            filetypes = [(self.supported_formats.get(ext, 'File'), f"*.{ext}")]
            filename = filedialog.asksaveasfilename(
                title=f"Export {data_type.title()} Data",
                filetypes=filetypes,
                defaultextension=f".{ext}"
            )
        
        if not filename:
            return False
        
        try:
            # Get data from DataProcessor based on type
            if data_type == 'raw':
                data = list(data_processor.raw_buffer)
            elif data_type == 'structured':
                data = list(data_processor.data_buffer) + list(data_processor.plot_buffer) + list(data_processor.meas_buffer)
                data = sorted(data, key=lambda x: x['timestamp'])
            elif data_type == 'data':
                data = list(data_processor.data_buffer)
            elif data_type == 'plot':
                data = list(data_processor.plot_buffer)
            elif data_type == 'meas':
                data = list(data_processor.meas_buffer)
            else:  # filtered
                data = list(data_processor.filtered_buffer)
            
            # Export the data
            if data_type in ['structured', 'data', 'plot', 'meas']:
                self._export_structured_data(filename, data, format_type)
            elif format_type.lower() == 'csv':
                self._export_csv(filename, data, data_type)
            elif format_type.lower() == 'json':
                self._export_json(filename, data)
            elif format_type.lower() == 'xlsx':
                self._export_excel(filename, data, data_type)
            else:
                # Default to text
                content = '\n'.join([entry.get('data', str(entry)) for entry in data])
                self._save_text(filename, content)
            
            # Add metadata if requested and format supports it
            if include_metadata and format_type.lower() in ['json', 'xlsx']:
                self._add_export_metadata(filename, format_type, data_processor)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
            return False
    
    def _add_export_metadata(self, filename, format_type, data_processor):
        """Add metadata to exported files"""
        stats = data_processor.get_statistics()
        
        if format_type.lower() == 'json':
            # Add metadata to existing JSON
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['export_metadata'] = {
                'export_time': datetime.now().isoformat(),
                'statistics': stats,
                'version': '1.0'
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format_type.lower() == 'xlsx':
            # Add metadata sheet to Excel file
            with pd.ExcelWriter(filename, mode='a', engine='openpyxl') as writer:
                metadata_df = pd.DataFrame([
                    {'Property': k, 'Value': v} for k, v in stats.items()
                ])
                metadata_df.to_excel(writer, sheet_name='Export_Metadata', index=False)
    
    def _export_structured_data(self, filename, data, format_type):
        """Export structured data (DATA/PLOT/MEAS entries)"""
        if format_type.lower() == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'type', 'name', 'value', 'raw_data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in data:
                    writer.writerow({
                        'timestamp': entry['timestamp'].isoformat(),
                        'type': entry.get('type', ''),
                        'name': entry.get('name', ''),
                        'value': entry.get('value', ''),
                        'raw_data': entry.get('raw_data', '')
                    })
        
        elif format_type.lower() == 'json':
            json_data = []
            for entry in data:
                json_entry = {
                    'timestamp': entry['timestamp'].isoformat(),
                    'type': entry.get('type', ''),
                    'name': entry.get('name', ''),
                    'value': entry.get('value', ''),
                    'raw_data': entry.get('raw_data', '')
                }
                json_data.append(json_entry)
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
        
        elif format_type.lower() == 'xlsx':
            # Prepare data for DataFrame
            excel_data = []
            for entry in data:
                excel_data.append({
                    'Timestamp': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'Type': entry.get('type', ''),
                    'Name': entry.get('name', ''),
                    'Value': entry.get('value', ''),
                    'Raw_Data': entry.get('raw_data', '')
                })
            
            if excel_data:
                df = pd.DataFrame(excel_data)
                
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # Main data sheet
                    df.to_excel(writer, sheet_name='Structured_Data', index=False)
                    
                    # Summary by type
                    if 'Type' in df.columns:
                        summary_data = df.groupby(['Type', 'Name']).agg({
                            'Value': ['count', 'min', 'max', 'mean', 'std']
                        }).round(3)
                        summary_data.to_excel(writer, sheet_name='Summary_by_Type')
            else:
                # Create empty Excel file
                df = pd.DataFrame({'Message': ['No structured data to export']})
                df.to_excel(filename, index=False)
        
        else:
            # Text format
            content = ""
            for entry in data:
                timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                content += f"[{timestamp}] [{entry.get('type', '')}] {entry.get('name', '')}: {entry.get('value', '')}\n"
            
            with open(filename, 'w', encoding='utf-8') as textfile:
                textfile.write(content)