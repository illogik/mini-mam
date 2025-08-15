import axios, { AxiosResponse } from 'axios';
import { Asset, AssetsResponse, FileRecord, FilesResponse } from '../types/api';

// Configure axios base URL - this will be the nginx proxy
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:80';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export class AssetsService {
  static async getAssets(page: number = 1, perPage: number = 10, search?: string): Promise<AssetsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString()
    });
    
    if (search && search.trim()) {
      params.append('search', search.trim());
    }
    
    const response = await api.get(`/api/assets/?${params.toString()}`);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async getAsset(id: string): Promise<Asset> {
    const response = await api.get(`/api/assets/${id}`);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async createAsset(assetData: Partial<Asset>): Promise<Asset> {
    const response = await api.post('/api/assets/', assetData);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async updateAsset(id: string, assetData: Partial<Asset>): Promise<Asset> {
    const response = await api.put(`/api/assets/${id}`, assetData);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async deleteAsset(id: string): Promise<void> {
    await api.delete(`/api/assets/${id}`);
  }
}



export class FilesService {
  static async getFiles(page: number = 1, perPage: number = 10): Promise<FilesResponse> {
    const response = await api.get(`/api/files/?page=${page}&per_page=${perPage}`);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async getFile(id: number): Promise<FileRecord> {
    const response = await api.get(`/api/files/${id}`);
    // The backend wraps data in a 'data' field due to create_response function
    return response.data.data || response.data;
  }

  static async generatePresignedUrl(filename: string, contentType?: string): Promise<{
    presigned_url: string;
    s3_key: string;
    unique_filename: string;
    original_filename: string;
  }> {
    const response = await api.post('/api/files/presigned-url', {
      filename,
      content_type: contentType
    });
    return response.data.data || response.data;
  }

  static async uploadToS3(presignedUrl: string, file: File): Promise<void> {
    // Upload directly to S3 using pre-signed URL
    await fetch(presignedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
      },
    });
  }

  static async completeUpload(uploadData: {
    s3_key: string;
    original_filename: string;
    unique_filename: string;
    file_size: number;
    mime_type: string;
    checksum: string;
    asset_id?: number;
  }): Promise<FileRecord> {
    const response = await api.post('/api/files/complete-upload', uploadData);
    return response.data.data || response.data;
  }

  static async uploadFile(file: File, assetId?: number): Promise<FileRecord> {
    // Step 1: Generate pre-signed URL
    const presignedData = await this.generatePresignedUrl(file.name, file.type);
    
    // Step 2: Upload directly to S3
    await this.uploadToS3(presignedData.presigned_url, file);
    
    // Step 3: Calculate file checksum
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const checksum = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    // Step 4: Complete upload by creating database record
    return await this.completeUpload({
      s3_key: presignedData.s3_key,
      original_filename: presignedData.original_filename,
      unique_filename: presignedData.unique_filename,
      file_size: file.size,
      mime_type: file.type || 'application/octet-stream',
      checksum,
      asset_id: assetId
    });
  }

  static async deleteFile(id: number): Promise<void> {
    await api.delete(`/api/files/${id}`);
  }

  static async downloadFile(id: number): Promise<Blob> {
    const response = await api.get(`/api/files/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export default api; 