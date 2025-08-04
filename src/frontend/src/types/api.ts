export interface Asset {
  id: string;
  name: string;
  description?: string;
  type: string;
  url: string;
  file_path: string;
  file_id?: number;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}



export interface AssetsResponse {
  assets: Asset[];
  total: number;
  page: number;
  per_page: number;
}

export interface FileRecord {
  id: number;
  filename: string;
  original_filename: string;
  s3_key: string;
  file_size: number;
  mime_type: string;
  checksum: string;
  asset_id?: number;
  created_at: string;
  updated_at: string;
}

export interface FilesResponse {
  files: FileRecord[];
  total: number;
  page: number;
  per_page: number;
}

 