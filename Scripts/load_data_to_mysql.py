"""
============================================================================
Student Result Analysis - MySQL Data Loader
============================================================================
Purpose: Load CSV data into MySQL database with proper error handling
Python Version: 3.8+
Dependencies: pandas, mysql-connector-python
============================================================================
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import sys
from datetime import datetime

# ============================================================================
# Database Configuration
# ============================================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',              # Change this to your MySQL username
    'password': '',  # Change this to your MySQL password
    'database': 'student_analysis'
}

# File configuration
CSV_FILE_PATH = 'students_data_cleaned.csv'
BATCH_SIZE = 1000  # Number of records to insert at once

# ============================================================================
# Helper Functions
# ============================================================================

def print_separator(char='=', length=70):
    """Print a separator line"""
    print(char * length)

def print_status(message, status='INFO'):
    """Print formatted status message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{status}] {message}")

def validate_csv_file(file_path):
    """Validate if CSV file exists and is readable"""
    try:
        df = pd.read_csv(file_path)
        print_status(f"✓ CSV file loaded successfully", "SUCCESS")
        print_status(f"  Total records: {len(df)}", "INFO")
        print_status(f"  Columns: {len(df.columns)}", "INFO")
        return df
    except FileNotFoundError:
        print_status(f"✗ File not found: {file_path}", "ERROR")
        sys.exit(1)
    except Exception as e:
        print_status(f"✗ Error reading CSV: {str(e)}", "ERROR")
        sys.exit(1)

def connect_to_database():
    """Establish connection to MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print_status(f"✓ Connected to MySQL Server version {db_info}", "SUCCESS")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()[0]
            print_status(f"  Using database: {database_name}", "INFO")
            return connection
    except Error as e:
        print_status(f"✗ Database connection failed: {str(e)}", "ERROR")
        print_status("  Please check your database credentials in DB_CONFIG", "HINT")
        sys.exit(1)

def prepare_data(df):
    """Clean and prepare data for MySQL insertion"""
    print_status("Preparing data for insertion...", "INFO")
    
    # Remove unnamed columns (index columns from CSV)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Replace NaN with None for proper NULL handling in MySQL
    df = df.where(pd.notnull(df), None)
    
    # Convert float columns to int where appropriate
    numeric_cols = ['NrSiblings', 'MathScore', 'ReadingScore', 'WritingScore']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
    
    print_status(f"✓ Data prepared: {len(df)} records ready", "SUCCESS")
    return df

def create_insert_query():
    """Create INSERT query with proper column names"""
    query = """
    INSERT INTO student_results 
    (Gender, EthnicGroup, ParentEduc, LunchType, TestPrep, 
     ParentMaritalStatus, PracticeSport, IsFirstChild, NrSiblings, 
     TransportMeans, WklyStudyHours, MathScore, ReadingScore, WritingScore)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return query

def insert_data_in_batches(connection, df, batch_size=BATCH_SIZE):
    """Insert data into MySQL in batches for better performance"""
    cursor = connection.cursor()
    insert_query = create_insert_query()
    
    # Convert DataFrame to list of tuples
    records = []
    for _, row in df.iterrows():
        record = (
            row.get('Gender'),
            row.get('EthnicGroup'),
            row.get('ParentEduc'),
            row.get('LunchType'),
            row.get('TestPrep'),
            row.get('ParentMaritalStatus'),
            row.get('PracticeSport'),
            row.get('IsFirstChild'),
            row.get('NrSiblings'),
            row.get('TransportMeans'),
            row.get('WklyStudyHours'),
            row.get('MathScore'),
            row.get('ReadingScore'),
            row.get('WritingScore')
        )
        records.append(record)
    
    total_records = len(records)
    inserted_count = 0
    failed_count = 0
    
    print_status(f"Starting batch insertion ({batch_size} records per batch)...", "INFO")
    print_separator('-')
    
    # Insert in batches
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        try:
            cursor.executemany(insert_query, batch)
            connection.commit()
            inserted_count += len(batch)
            progress = (inserted_count / total_records) * 100
            print_status(f"Progress: {inserted_count}/{total_records} ({progress:.1f}%)", "INFO")
        except Error as e:
            failed_count += len(batch)
            print_status(f"✗ Batch insertion failed: {str(e)}", "ERROR")
    
    cursor.close()
    
    print_separator('-')
    print_status(f"✓ Insertion completed", "SUCCESS")
    print_status(f"  Successfully inserted: {inserted_count} records", "INFO")
    if failed_count > 0:
        print_status(f"  Failed records: {failed_count}", "WARNING")
    
    return inserted_count, failed_count

def verify_data_load(connection):
    """Verify data was loaded correctly"""
    print_separator('=')
    print_status("Verifying data load...", "INFO")
    
    cursor = connection.cursor()
    
    # Count total records
    cursor.execute("SELECT COUNT(*) FROM student_results")
    total_count = cursor.fetchone()[0]
    print_status(f"✓ Total records in database: {total_count}", "SUCCESS")
    
    # Sample records
    cursor.execute("SELECT * FROM student_results LIMIT 5")
    print_status("Sample records (first 5):", "INFO")
    columns = [desc[0] for desc in cursor.description]
    print(f"\n{'ID':<6} {'Gender':<10} {'Math':<6} {'Reading':<8} {'Writing':<8} {'AvgScore':<10}")
    print_separator('-')
    
    for row in cursor.fetchall():
        print(f"{row[0]:<6} {str(row[1]):<10} {row[12]:<6} {row[13]:<8} {row[14]:<8} {float(row[16]):<10.2f}")
    
    # Basic statistics
    cursor.execute("""
        SELECT 
            ROUND(AVG(MathScore), 2) as avg_math,
            ROUND(AVG(ReadingScore), 2) as avg_reading,
            ROUND(AVG(WritingScore), 2) as avg_writing
        FROM student_results
    """)
    stats = cursor.fetchone()
    print(f"\nAverage Scores:")
    print(f"  Math: {stats[0]}")
    print(f"  Reading: {stats[1]}")
    print(f"  Writing: {stats[2]}")
    
    cursor.close()

def clear_existing_data(connection):
    """Clear existing data from table (optional)"""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM student_results")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print_separator('=')
        print_status(f"Found {existing_count} existing records in database", "WARNING")
        response = input("Do you want to clear existing data? (yes/no): ").lower()
        
        if response == 'yes':
            cursor.execute("TRUNCATE TABLE student_results")
            connection.commit()
            print_status("✓ Existing data cleared", "SUCCESS")
        else:
            print_status("Keeping existing data. New records will be appended.", "INFO")
    
    cursor.close()

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function"""
    print_separator('=')
    print("STUDENT RESULT ANALYSIS - MySQL Data Loader")
    print_separator('=')
    print()
    
    start_time = datetime.now()
    
    try:
        # Step 1: Validate and load CSV
        print_status("Step 1: Loading CSV file...", "INFO")
        df = validate_csv_file(CSV_FILE_PATH)
        print()
        
        # Step 2: Connect to database
        print_status("Step 2: Connecting to MySQL database...", "INFO")
        connection = connect_to_database()
        print()
        
        # Step 3: Clear existing data (optional)
        clear_existing_data(connection)
        print()
        
        # Step 4: Prepare data
        print_status("Step 3: Preparing data...", "INFO")
        df_clean = prepare_data(df)
        print()
        
        # Step 5: Insert data
        print_status("Step 4: Inserting data into database...", "INFO")
        inserted, failed = insert_data_in_batches(connection, df_clean)
        print()
        
        # Step 6: Verify data load
        print_status("Step 5: Verifying data load...", "INFO")
        verify_data_load(connection)
        print()
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Final summary
        print_separator('=')
        print_status("DATA LOAD COMPLETED SUCCESSFULLY!", "SUCCESS")
        print_status(f"Total time taken: {duration:.2f} seconds", "INFO")
        print_status(f"Records processed: {inserted}", "INFO")
        print_separator('=')
        
        # Close connection
        if connection.is_connected():
            connection.close()
            print_status("Database connection closed", "INFO")
    
    except KeyboardInterrupt:
        print_status("\n\n✗ Operation cancelled by user", "WARNING")
        sys.exit(0)
    except Exception as e:
        print_status(f"✗ Unexpected error: {str(e)}", "ERROR")
        sys.exit(1)

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
