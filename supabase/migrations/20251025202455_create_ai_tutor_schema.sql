/*
  # AI Tutor Application Schema

  ## Overview
  This migration creates the complete database schema for an AI-powered tutoring application with user management, chat history, quiz functionality, and progress tracking.

  ## New Tables

  1. **users**
     - `id` (uuid, primary key) - Unique user identifier
     - `email` (text, unique) - User email address
     - `name` (text) - User's full name
     - `picture` (text, nullable) - Profile picture URL
     - `learning_interests` (text array) - Topics user is interested in
     - `created_at` (timestamptz) - Account creation timestamp

  2. **sessions**
     - `id` (uuid, primary key) - Session identifier
     - `session_token` (text, unique) - OAuth session token
     - `user_id` (uuid, foreign key) - Reference to users table
     - `expires_at` (timestamptz) - Session expiration time
     - `created_at` (timestamptz) - Session creation timestamp

  3. **chat_history**
     - `id` (uuid, primary key) - Chat conversation identifier
     - `user_id` (uuid, foreign key) - Reference to users table
     - `topic` (text) - Subject being discussed
     - `messages` (jsonb) - Array of chat messages with role, content, timestamp
     - `created_at` (timestamptz) - Chat creation timestamp

  4. **quiz_results**
     - `id` (uuid, primary key) - Quiz result identifier
     - `user_id` (uuid, foreign key) - Reference to users table
     - `topic` (text) - Quiz subject
     - `score` (integer) - Points earned
     - `total` (integer) - Total possible points
     - `questions` (jsonb) - Quiz questions and answers
     - `created_at` (timestamptz) - Quiz completion timestamp

  5. **progress**
     - `id` (uuid, primary key) - Progress record identifier
     - `user_id` (uuid, unique, foreign key) - Reference to users table
     - `xp_points` (integer) - Total experience points earned
     - `topics_learned` (text array) - List of topics studied
     - `learning_streak` (integer) - Consecutive days of activity
     - `last_activity` (timestamptz) - Last activity timestamp

  ## Security
  - Enable RLS on all tables
  - Users can only access their own data
  - Authenticated users required for all operations
  - Session-based authentication with expiration checks
*/

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  name text NOT NULL,
  picture text,
  learning_interests text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_token text UNIQUE NOT NULL,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic text NOT NULL,
  messages jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- Create quiz_results table
CREATE TABLE IF NOT EXISTS quiz_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic text NOT NULL,
  score integer NOT NULL DEFAULT 0,
  total integer NOT NULL DEFAULT 0,
  questions jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- Create progress table
CREATE TABLE IF NOT EXISTS progress (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  xp_points integer DEFAULT 0,
  topics_learned text[] DEFAULT '{}',
  learning_streak integer DEFAULT 0,
  last_activity timestamptz DEFAULT now()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_user_id ON progress(user_id);

-- Enable Row Level Security on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- RLS Policies for sessions table
CREATE POLICY "Users can view own sessions"
  ON sessions FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
  ON sessions FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions"
  ON sessions FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- RLS Policies for chat_history table
CREATE POLICY "Users can view own chat history"
  ON chat_history FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chat history"
  ON chat_history FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chat history"
  ON chat_history FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policies for quiz_results table
CREATE POLICY "Users can view own quiz results"
  ON quiz_results FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own quiz results"
  ON quiz_results FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- RLS Policies for progress table
CREATE POLICY "Users can view own progress"
  ON progress FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own progress"
  ON progress FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress"
  ON progress FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);