-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 15, 2025 at 04:38 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `education`
--

-- --------------------------------------------------------

--
-- Table structure for table `admission_applications`
--

CREATE TABLE `admission_applications` (
  `id` int(11) NOT NULL,
  `fullname` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `program` varchar(255) NOT NULL,
  `application_date` date NOT NULL,
  `status` varchar(50) DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `blogs`
--

CREATE TABLE `blogs` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `author` varchar(100) NOT NULL,
  `excerpt` text NOT NULL,
  `link` varchar(255) NOT NULL,
  `publish_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `blogs`
--

INSERT INTO `blogs` (`id`, `title`, `author`, `excerpt`, `link`, `publish_date`) VALUES
(1, 'Choosing a College', 'John Doe', 'Tips for selecting the right college.', 'http://example.com/blog1', '2023-10-01');

-- --------------------------------------------------------

--
-- Table structure for table `colleges`
--

CREATE TABLE `colleges` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `courses_offered` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `colleges`
--

INSERT INTO `colleges` (`id`, `name`, `location`, `courses_offered`) VALUES
(1, 'St. Xavier’s College', 'Kathmandu', 'BSc CSIT, BCA'),
(2, 'Kathmandu University', 'Lalitpur', 'BBA, BJMC'),
(3, 'Kathmandu Medical College', 'Kathmandu', 'MBBS'),
(4, 'Tribhuvan University', 'Kathmandu', 'BBS, BFA');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `id` int(11) NOT NULL,
  `category` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `duration` varchar(50) NOT NULL,
  `fees` varchar(100) NOT NULL,
  `colleges` text NOT NULL,
  `admission` text NOT NULL,
  `eligibility` text NOT NULL,
  `career_options` text NOT NULL,
  `syllabus` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`id`, `category`, `name`, `description`, `duration`, `fees`, `colleges`, `admission`, `eligibility`, `career_options`, `syllabus`) VALUES
(1, 'Science and Technology', 'BSc CSIT', 'Bachelor of Science in Computer Science and Information Technology', '4 years', 'NRP 500,000', 'Tribhuvan University, St. Xavier’s College', 'Entrance exam required', '10+2 with Science (Math/Physics)', 'Software Developer, IT Manager', 'http://www.example.com/syllabus/bsc-csit'),
(2, 'Management and Business', 'BBA', 'Bachelor of Business Administration', '4 years', 'NRP 600,000', 'Kathmandu University', 'Entrance exam and interview', '10+2 in any stream', 'Manager, Entrepreneur', 'http://www.example.com/syllabus/bba'),
(3, 'Science and Technology', 'BCA', 'Bachelor of Computer Applications', '3 years', 'NRP 450,000', 'Purbanchal University', 'Entrance exam required', '10+2 with Mathematics', 'Software Developer, Web Developer', 'http://www.example.com/syllabus/bca'),
(4, 'Health Sciences', 'MBBS', 'Bachelor of Medicine, Bachelor of Surgery', '5.5 years', 'NRP 4,000,000', 'Kathmandu Medical College', 'Entrance exam required', '10+2 with Science (Biology)', 'Doctor, Surgeon', 'http://www.example.com/syllabus/mbbs'),
(5, 'Management and Business', 'BBS', 'Bachelor of Business Studies', '4 years', 'NRP 400,000', 'Tribhuvan University', 'Entrance exam required', '10+2 in any stream', 'Accountant, Business Analyst', 'http://www.example.com/syllabus/bbs'),
(6, 'Media and Communication', 'BJMC', 'Bachelor of Journalism and Mass Communication', '3 years', 'NRP 350,000', 'Kathmandu University', 'Entrance exam required', '10+2 in any stream', 'Journalist, Media Producer', 'http://www.example.com/syllabus/bjmc'),
(7, 'Fine Arts and Design', 'BFA', 'Bachelor of Fine Arts', '4 years', 'NRP 500,000', 'Tribhuvan University', 'Portfolio and entrance exam', '10+2 in any stream', 'Artist, Designer', 'http://www.example.com/syllabus/bfa');

-- --------------------------------------------------------

--
-- Table structure for table `enrollment_requests`
--

CREATE TABLE `enrollment_requests` (
  `id` int(11) NOT NULL,
  `fullname` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `program` varchar(255) NOT NULL,
  `request_date` date NOT NULL,
  `status` varchar(50) DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `enrollment_requests`
--

INSERT INTO `enrollment_requests` (`id`, `fullname`, `email`, `program`, `request_date`, `status`) VALUES
(1, 'Bishal Lama', 'bishal.lama@example.com', 'BCA', '2025-04-15', 'pending');

-- --------------------------------------------------------

--
-- Table structure for table `support_queries`
--

CREATE TABLE `support_queries` (
  `id` int(11) NOT NULL,
  `user_name` varchar(255) NOT NULL,
  `query` text NOT NULL,
  `intent` varchar(50) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `universities`
--

CREATE TABLE `universities` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `established_year` int(11) NOT NULL,
  `description` text NOT NULL,
  `website` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `universities`
--

INSERT INTO `universities` (`id`, `name`, `location`, `established_year`, `description`, `website`) VALUES
(1, 'Tribhuvan University', 'Kathmandu', 1959, 'Oldest university in Nepal.', 'http://www.tu.edu.np');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admission_applications`
--
ALTER TABLE `admission_applications`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `blogs`
--
ALTER TABLE `blogs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `colleges`
--
ALTER TABLE `colleges`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_name` (`name`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_name` (`name`);

--
-- Indexes for table `enrollment_requests`
--
ALTER TABLE `enrollment_requests`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `support_queries`
--
ALTER TABLE `support_queries`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `universities`
--
ALTER TABLE `universities`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_name` (`name`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admission_applications`
--
ALTER TABLE `admission_applications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `blogs`
--
ALTER TABLE `blogs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `colleges`
--
ALTER TABLE `colleges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `enrollment_requests`
--
ALTER TABLE `enrollment_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `support_queries`
--
ALTER TABLE `support_queries`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `universities`
--
ALTER TABLE `universities`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
