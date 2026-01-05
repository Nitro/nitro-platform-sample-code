/**
 * Common helper utilities for document processing scripts.
 */

import { readdir, mkdir, stat } from 'fs/promises';
import { join } from 'path';

/**
 * Check if a filename matches any of the given glob patterns.
 * @param filename - Name of the file to check.
 * @param patterns - Array of glob patterns (e.g., ['*.docx', '*.pdf']).
 * @returns True if filename matches any pattern.
 */
function matchesPattern(filename: string, patterns: string[]): boolean {
  for (const pattern of patterns) {
    // Convert simple glob pattern to regex
    // This handles basic * wildcard matching
    const regexPattern = pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '.*');
    const regex = new RegExp(`^${regexPattern}$`, 'i');
    
    if (regex.test(filename)) {
      return true;
    }
  }
  return false;
}

/**
 * Recursively find files matching patterns in a directory.
 * @param dir - Directory to search.
 * @param patterns - Array of glob patterns.
 * @param files - Accumulator for found files (used internally).
 * @returns Array of file paths.
 */
async function findMatchingFiles(
  dir: string,
  patterns: string[],
  files: string[] = []
): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    
    if (entry.isDirectory()) {
      // Recursively search subdirectories
      await findMatchingFiles(fullPath, patterns, files);
    } else if (entry.isFile() && matchesPattern(entry.name, patterns)) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Validate input folder and setup output folder. Returns list of files to process.
 * @param inputFolder - Path to the input directory containing files to process.
 * @param outputFolder - Path to the output directory for processed files.
 * @param filePatterns - List of glob patterns to match files (e.g., ['*.docx', '*.pdf']).
 *                       If not provided, defaults to common Office document formats.
 * @returns Array of file paths for files matching the patterns.
 * @throws Error if input folder is invalid or no matching files are found.
 */
export async function validateAndSetup(
  inputFolder: string,
  outputFolder: string,
  filePatterns?: string[]
): Promise<string[]> {
  // Default patterns for Office documents if none provided
  const patterns = filePatterns || ['*.docx', '*.doc', '*.xlsx', '*.xls', '*.pptx', '*.ppt'];

  // Validate input folder exists
  try {
    const inputStat = await stat(inputFolder);
    if (!inputStat.isDirectory()) {
      console.error(`❌ Error: Invalid input folder: ${inputFolder}`);
      process.exit(1);
    }
  } catch (error) {
    console.error(`❌ Error: Invalid input folder: ${inputFolder}`);
    process.exit(1);
  }

  // Create output folder if needed
  try {
    await mkdir(outputFolder, { recursive: true });
  } catch (error) {
    console.error(`❌ Error: Could not create output folder: ${outputFolder}`);
    process.exit(1);
  }

  // Find all matching files
  const files = await findMatchingFiles(inputFolder, patterns);

  if (files.length === 0) {
    console.error(`❌ No files matching patterns ${patterns.join(', ')} found in ${inputFolder}`);
    process.exit(1);
  }

  return files;
}
