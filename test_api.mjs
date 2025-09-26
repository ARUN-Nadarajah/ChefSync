import fetch from 'node-fetch';

const testAPI = async () => {
  try {
    console.log('Testing document types API...');
    const response = await fetch('http://127.0.0.1:8000/api/auth/documents/types/?role=cook', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers));
    
    if (response.ok) {
      const data = await response.json();
      console.log('Document types:', JSON.stringify(data, null, 2));
    } else {
      const errorText = await response.text();
      console.log('Error response:', errorText);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};

testAPI();