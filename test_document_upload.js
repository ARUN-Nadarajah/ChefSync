const testDocumentUpload = async () => {
  const apiUrl = 'http://127.0.0.1:8000';
  
  // First, let's test if we can get document types
  try {
    console.log('Testing document types endpoint...');
    const response = await fetch(`${apiUrl}/api/auth/documents/types/?role=cook`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Document types response:', data);
    } else {
      console.error('Document types error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error response:', errorText);
    }
  } catch (error) {
    console.error('Document types fetch error:', error);
  }
  
  // Test the upload endpoint with mock data
  try {
    console.log('\nTesting upload endpoint with FormData...');
    
    // Create a test file (blob)
    const testFile = new Blob(['test content'], { type: 'text/plain' });
    const formData = new FormData();
    formData.append('file_upload', testFile, 'test.txt');
    formData.append('document_type_id', '1');
    formData.append('user_email', 'test@example.com');
    
    const uploadResponse = await fetch(`${apiUrl}/api/auth/documents/upload-registration/`, {
      method: 'POST',
      body: formData,
    });
    
    console.log('Upload response status:', uploadResponse.status);
    
    if (uploadResponse.ok) {
      const uploadData = await uploadResponse.json();
      console.log('Upload success:', uploadData);
    } else {
      const uploadError = await uploadResponse.text();
      console.error('Upload error:', uploadError);
    }
  } catch (error) {
    console.error('Upload fetch error:', error);
  }
};

testDocumentUpload();