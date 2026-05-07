-- ═══════════════════════════════════════════════════════════════════════════════
-- Supabase RLS Policy Fix for NEXUS
-- ═══════════════════════════════════════════════════════════════════════════════
-- Run this in your Supabase SQL Editor after unpausing the project.
-- https://app.supabase.com -> SQL Editor -> new query -> paste this -> Run

-- Enable Row-Level Security on the documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy 1: Allow public SELECT (for reading documents in chat)
CREATE POLICY "Enable public read access"
  ON documents
  FOR SELECT
  USING (true);

-- Policy 2: Only authenticated users can INSERT
CREATE POLICY "Enable insert for authenticated users only"
  ON documents
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Policy 3: Only document owner can UPDATE
CREATE POLICY "Enable update for own documents"
  ON documents
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy 4: Only document owner can DELETE
CREATE POLICY "Enable delete for own documents"
  ON documents
  FOR DELETE
  USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- For demo mode (public document access), you can relax this:
-- If you want demo documents to be completely public-readable, keep Policy 1 above.
-- The frontend uses the anon key (public), so SELECT will work.
-- ═══════════════════════════════════════════════════════════════════════════════
