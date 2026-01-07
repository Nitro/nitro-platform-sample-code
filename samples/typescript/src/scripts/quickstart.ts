#!/usr/bin/env node
/**
 * Quickstart script to test Nitro Platform API authentication and connection.
 */

import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const BASE_URL = process.env.PLATFORM_BASE_URL || 'https://api.gonitro.dev';
const CLIENT_ID = process.env.PLATFORM_CLIENT_ID;
const CLIENT_SECRET = process.env.PLATFORM_CLIENT_SECRET;

/**
 * Get OAuth2 access token using client credentials.
 * @returns Access token string.
 */
async function getAccessToken(): Promise<string> {
  const url = `${BASE_URL}/oauth/token`;
  const data = {
    clientID: CLIENT_ID,
    clientSecret: CLIENT_SECRET,
  };

  const response = await axios.post(url, data);
  return response.data.accessToken;
}

/**
 * Test API connection with a simple request.
 * @param token - OAuth2 access token.
 * @returns True if connection is successful.
 */
async function testConnection(token: string): Promise<boolean> {
  const url = `${BASE_URL}/jobs/test-job-id/status`;
  const headers = { Authorization: `Bearer ${token}` };

  try {
    await axios.get(url, { headers });
    return true;
  } catch (error: any) {
    // 404 is expected for non-existent job, but proves auth works
    if (error.response?.status === 404) {
      console.log('✅ Authentication successful (404 expected for test job ID)');
      return true;
    }
    throw error;
  }
}

/**
 * Main function to test API authentication and connection.
 */
async function main(): Promise<void> {
  if (!CLIENT_ID || !CLIENT_SECRET) {
    console.log('❌ Missing credentials!');
    console.log('To get your credentials:');
    console.log('1. Go to https://admin.gonitro.com');
    console.log('2. Navigate to Settings → API');
    console.log("3. Click 'Create Application'");
    console.log('4. Name your application and save the Client ID and Client Secret');
    console.log('5. Set environment variables:');
    console.log('   export PLATFORM_CLIENT_ID=<YOUR_CLIENT_ID>');
    console.log('   export PLATFORM_CLIENT_SECRET=<YOUR_CLIENT_SECRET>');
    return;
  }

  try {
    console.log('🔐 Getting access token...');
    const token = await getAccessToken();
    console.log('✅ Token obtained successfully');

    console.log('🧪 Testing API connection...');
    await testConnection(token);
    console.log('✅ API connection successful');

    console.log('\n🎉 Setup complete! You can now use the Platform API.');
    console.log('📖 See https://developers.gonitro.com/docs for API documentation');
  } catch (error: any) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

main();
