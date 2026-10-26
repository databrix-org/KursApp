import pandas as pd
import json
import os
from pathlib import Path
from load_data import read_table

class Database:

    def __init__(self, data_path: str = ".", config_file: str = None):
        """
        Initialize Database with optional config file or auto-detect CSV files
        
        Args:
            data_path: Path to directory containing CSV files
            config_file: Optional config file specifying table names
        """
        self.data_path = Path(data_path)
        self.config_file = config_file
        self.table_names = []
        self.tables = {}

    def _auto_detect_tables(self):
        """Auto-detect CSV files in the data directory"""
        csv_files = list(self.data_path.glob("*.csv"))
        self.table_names = [file.stem for file in csv_files]
        print(f"Auto-detected tables: {self.table_names}")

    def _extract_config_file(self):
        """Extract table names from config file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        
        with open(self.config_file) as json_file:
            self.database_config = json.load(json_file)
            self.table_names = self.database_config.get("table", [])

    def _extract_tables(self):
        """Load all tables into memory"""
        if not self.table_names:
            print("No tables to load")
            return
            
        for table_name in self.table_names:
            try:
                self.tables[table_name] = read_table(table_name, base_path=str(self.data_path))
            except Exception as e:
                print(f"Warning: Could not load table '{table_name}': {e}")
        
        print(f"Successfully loaded {len(self.tables)} tables")

    def load(self, auto_detect: bool = True):
        """
        Load database tables
        
        Args:
            auto_detect: If True, auto-detect CSV files. If False, use config file.
        """
        if auto_detect and not self.config_file:
            self._auto_detect_tables()
        elif self.config_file:
            self._extract_config_file()
        else:
            raise ValueError("Either provide config_file or enable auto_detect")
            
        self._extract_tables()

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Get a specific table"""
        if table_name not in self.tables:
            raise KeyError(f"Table '{table_name}' not found. Available tables: {list(self.tables.keys())}")
        return self.tables[table_name]

    def list_tables(self) -> list:
        """List all available table names"""
        return list(self.tables.keys())

    def get_table_info(self) -> dict:
        """Get basic info about all loaded tables"""
        info = {}
        for name, table in self.tables.items():
            info[name] = {
                'rows': len(table),
                'columns': len(table.columns),
                'column_names': list(table.columns)
            }
        return info

