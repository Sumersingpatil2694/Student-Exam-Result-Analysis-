-- ============================================================================
-- MySQL Database Setup Script
-- Project: Student Result Analysis
-- Purpose: Create database, table structure, and indexes
-- Author: Sumersing Patil
-- Created: January 2026
-- ============================================================================

-- Step 1: Create Database
-- ============================================================================
DROP DATABASE IF EXISTS student_analysis;
CREATE DATABASE student_analysis;
USE student_analysis;

-- Verify database creation
SELECT DATABASE() AS current_database;

-- Step 2: Create Main Table
-- ============================================================================
CREATE TABLE student_results (
    -- Primary Key
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Demographic Information
    Gender VARCHAR(10),
    EthnicGroup VARCHAR(10),
    
    -- Family Background
    ParentEduc VARCHAR(50),
    ParentMaritalStatus VARCHAR(20),
    IsFirstChild VARCHAR(5),
    NrSiblings INT,
    
    -- Socioeconomic Factors
    LunchType VARCHAR(20),
    TransportMeans VARCHAR(20),
    
    -- Academic Preparation
    TestPrep VARCHAR(20),
    WklyStudyHours VARCHAR(10),
    PracticeSport VARCHAR(20),
    
    -- Exam Scores
    MathScore INT CHECK (MathScore >= 0 AND MathScore <= 100),
    ReadingScore INT CHECK (ReadingScore >= 0 AND ReadingScore <= 100),
    WritingScore INT CHECK (WritingScore >= 0 AND WritingScore <= 100),
    
    -- Derived Columns (can be calculated)
    TotalScore INT GENERATED ALWAYS AS (MathScore + ReadingScore + WritingScore) STORED,
    AvgScore DECIMAL(5,2) GENERATED ALWAYS AS ((MathScore + ReadingScore + WritingScore) / 3) STORED,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Step 3: Create Indexes for Performance Optimization
-- ============================================================================
-- Indexes on frequently queried columns
CREATE INDEX idx_gender ON student_results(Gender);
CREATE INDEX idx_ethnic_group ON student_results(EthnicGroup);
CREATE INDEX idx_parent_educ ON student_results(ParentEduc);
CREATE INDEX idx_lunch_type ON student_results(LunchType);
CREATE INDEX idx_test_prep ON student_results(TestPrep);
CREATE INDEX idx_study_hours ON student_results(WklyStudyHours);

-- Composite index for common query patterns
CREATE INDEX idx_gender_testprep ON student_results(Gender, TestPrep);
CREATE INDEX idx_lunch_testprep ON student_results(LunchType, TestPrep);

-- Index on scores for performance queries
CREATE INDEX idx_math_score ON student_results(MathScore);
CREATE INDEX idx_avg_score ON student_results(AvgScore);

-- Step 4: Verify Table Structure
-- ============================================================================
DESCRIBE student_results;
SHOW INDEXES FROM student_results;

-- Step 5: Create Views for Common Queries
-- ============================================================================

-- View 1: Student Performance Summary
CREATE OR REPLACE VIEW vw_performance_summary AS
SELECT 
    student_id,
    Gender,
    EthnicGroup,
    TestPrep,
    LunchType,
    MathScore,
    ReadingScore,
    WritingScore,
    TotalScore,
    AvgScore,
    CASE 
        WHEN AvgScore >= 80 THEN 'Excellent'
        WHEN AvgScore >= 60 THEN 'Good'
        WHEN AvgScore >= 40 THEN 'Average'
        ELSE 'Poor'
    END AS PerformanceCategory
FROM student_results;

-- View 2: Gender-wise Performance Statistics
CREATE OR REPLACE VIEW vw_gender_performance AS
SELECT 
    Gender,
    COUNT(*) AS total_students,
    ROUND(AVG(MathScore), 2) AS avg_math,
    ROUND(AVG(ReadingScore), 2) AS avg_reading,
    ROUND(AVG(WritingScore), 2) AS avg_writing,
    ROUND(AVG(AvgScore), 2) AS overall_avg,
    MIN(AvgScore) AS min_score,
    MAX(AvgScore) AS max_score
FROM student_results
WHERE Gender IS NOT NULL
GROUP BY Gender;

-- View 3: Test Preparation Impact Analysis
CREATE OR REPLACE VIEW vw_test_prep_impact AS
SELECT 
    TestPrep,
    COUNT(*) AS student_count,
    ROUND(AVG(MathScore), 2) AS avg_math,
    ROUND(AVG(ReadingScore), 2) AS avg_reading,
    ROUND(AVG(WritingScore), 2) AS avg_writing,
    ROUND(AVG(AvgScore), 2) AS overall_avg
FROM student_results
WHERE TestPrep IS NOT NULL
GROUP BY TestPrep;

-- View 4: Top Performers
CREATE OR REPLACE VIEW vw_top_performers AS
SELECT 
    student_id,
    Gender,
    EthnicGroup,
    ParentEduc,
    TestPrep,
    WklyStudyHours,
    MathScore,
    ReadingScore,
    WritingScore,
    TotalScore,
    AvgScore
FROM student_results
WHERE AvgScore >= 80
ORDER BY AvgScore DESC;

-- View 5: At-Risk Students
CREATE OR REPLACE VIEW vw_at_risk_students AS
SELECT 
    student_id,
    Gender,
    EthnicGroup,
    LunchType,
    TestPrep,
    WklyStudyHours,
    MathScore,
    ReadingScore,
    WritingScore,
    AvgScore
FROM student_results
WHERE AvgScore < 40
ORDER BY AvgScore ASC;

-- Step 6: Create Stored Procedures
-- ============================================================================

-- Procedure 1: Get Student Performance by ID
DELIMITER //
CREATE PROCEDURE sp_get_student_performance(IN p_student_id INT)
BEGIN
    SELECT 
        student_id,
        Gender,
        EthnicGroup,
        ParentEduc,
        LunchType,
        TestPrep,
        WklyStudyHours,
        MathScore,
        ReadingScore,
        WritingScore,
        TotalScore,
        AvgScore,
        CASE 
            WHEN AvgScore >= 80 THEN 'Excellent'
            WHEN AvgScore >= 60 THEN 'Good'
            WHEN AvgScore >= 40 THEN 'Average'
            ELSE 'Poor'
        END AS PerformanceCategory
    FROM student_results
    WHERE student_id = p_student_id;
END //
DELIMITER ;

-- Procedure 2: Get Performance Statistics by Gender
DELIMITER //
CREATE PROCEDURE sp_gender_statistics()
BEGIN
    SELECT * FROM vw_gender_performance;
END //
DELIMITER ;

-- Procedure 3: Get Top N Performers
DELIMITER //
CREATE PROCEDURE sp_top_performers(IN n INT)
BEGIN
    SELECT 
        student_id,
        Gender,
        EthnicGroup,
        TestPrep,
        MathScore,
        ReadingScore,
        WritingScore,
        TotalScore,
        AvgScore
    FROM student_results
    ORDER BY TotalScore DESC
    LIMIT n;
END //
DELIMITER ;

-- Step 7: Sample Data Verification (run after loading data)
-- ============================================================================

-- Uncomment these queries after loading data to verify

-- SELECT COUNT(*) AS total_records FROM student_results;
-- SELECT * FROM student_results LIMIT 10;
-- SELECT * FROM vw_performance_summary LIMIT 10;
-- SELECT * FROM vw_gender_performance;
-- SELECT * FROM vw_test_prep_impact;
-- CALL sp_get_student_performance(1);
-- CALL sp_top_performers(10);

-- ============================================================================
-- End of Setup Script
-- ============================================================================

-- Display success message
SELECT 'Database setup completed successfully!' AS Status,
       'student_analysis' AS Database_Name,
       'student_results' AS Main_Table,
       '5 Views Created' AS Views,
       '3 Stored Procedures Created' AS Procedures;

-- Show table statistics
SELECT 
    TABLE_NAME,
    ENGINE,
    TABLE_ROWS,
    AVG_ROW_LENGTH,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'student_analysis'
AND TABLE_NAME = 'student_results';
