import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import webbrowser

class SonarRulesExtractor:
    def __init__(self):
        self.base_url = "https://rules.sonarsource.com/python"
        self.rules = pd.DataFrame()  # Initialize as empty DataFrame
        
    def fetch_rules(self):
        """Fetch all rules from SonarSource Python rules page"""
        try:
            # Try to get the first page
            response = requests.get(self.base_url)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table containing the rules
            rules_table = soup.find('table', {'class': 'rules'})
            if not rules_table:
                return "Could not find rules table on the page"
            
            # Extract table headers
            headers = []
            header_row = rules_table.find('thead').find('tr')
            for th in header_row.find_all('th'):
                headers.append(th.text.strip())
            
            # Add link column to headers
            headers.append("Link")
            
            # Extract table rows
            rows = []
            tbody = rules_table.find('tbody')
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == len(headers) - 1:  # -1 because we added Link column
                    row_data = [col.text.strip() for col in cols]
                    
                    # Extract link if available
                    link = cols[1].find('a')
                    if link and 'href' in link.attrs:
                        row_data.append("https://rules.sonarsource.com" + link['href'])
                    else:
                        row_data.append("")
                        
                    rows.append(row_data)
            
            # Create DataFrame
            if rows:
                self.rules = pd.DataFrame(rows, columns=headers)
                return f"Successfully extracted {len(self.rules)} rules"
            else:
                return "No rules found on the page"
            
        except requests.RequestException as e:
            return f"Error fetching data: {str(e)}"
        except Exception as e:
            return f"Error parsing data: {str(e)}"

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SonarSource Python Rules Extractor")
        self.geometry("1200x800")
        self.configure(bg="#f0f0f0")
        
        self.extractor = SonarRulesExtractor()
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="SonarSource Python Rules Extractor", 
                              font=("Arial", 16, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Button frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.fetch_button = tk.Button(button_frame, text="Fetch Rules", command=self.start_fetching,
                                     bg="#3498db", fg="white", font=("Arial", 12), padx=15, pady=8)
        self.fetch_button.pack(side=tk.LEFT, padx=5)
        
        self.export_button = tk.Button(button_frame, text="Export to CSV", command=self.export_csv,
                                      bg="#27ae60", fg="white", font=("Arial", 12), padx=15, pady=8, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = tk.Frame(self, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="Ready to fetch rules", font=("Arial", 10), 
                                    fg="#7f8c8d", bg="#f0f0f0")
        self.status_label.pack(side=tk.LEFT)
        
        # Rules display
        self.tree = ttk.Treeview(self, show="headings", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Footer
        footer_frame = tk.Frame(self, bg="#ecf0f1", height=40)
        footer_frame.pack(fill=tk.X, padx=10, pady=10)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(footer_frame, text="Note: Double-click on a rule to open its details in a browser", 
                               font=("Arial", 9), fg="#7f8c8d", bg="#ecf0f1")
        footer_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Configure treeview style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Treeview", font=("Arial", 9), rowheight=25)
        
    def start_fetching(self):
        """Start fetching rules in a separate thread"""
        self.status_label.config(text="Fetching rules...")
        self.fetch_button.config(state=tk.DISABLED)
        
        # Run fetching in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=self.fetch_rules)
        thread.daemon = True
        thread.start()
        
    def fetch_rules(self):
        """Fetch rules and update UI"""
        result = self.extractor.fetch_rules()
        
        # Update UI in the main thread
        self.after(0, self.update_ui, result)
        
    def update_ui(self, result):
        """Update UI with fetched rules"""
        self.status_label.config(text=result)
        self.fetch_button.config(state=tk.NORMAL)
        
        # Check if we have rules
        if not self.extractor.rules.empty:
            self.export_button.config(state=tk.NORMAL)
            self.display_rules()
        else:
            messagebox.showerror("Error", result)
            
    def display_rules(self):
        """Display rules in the treeview"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Set up columns
        columns = list(self.extractor.rules.columns)
        self.tree["columns"] = columns
        
        # Format columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, minwidth=80, anchor=tk.W)
            
        # Add data to treeview
        for _, row in self.extractor.rules.iterrows():
            self.tree.insert("", tk.END, values=list(row))
                
    def on_double_click(self, event):
        """Handle double-click on a rule to open its details"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            
            # The link is in the last column
            if values and len(values) > 0:
                link = values[-1]
                if link and link.startswith("http"):
                    webbrowser.open(link)
            
    def export_csv(self):
        """Export rules to CSV file"""
        if not self.extractor.rules.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sonarqube_python_rules_{timestamp}.csv"
            try:
                self.extractor.rules.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Rules exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No rules to export")

if __name__ == "__main__":
    app = Application()
    app.mainloop()