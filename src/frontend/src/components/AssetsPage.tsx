import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AssetsService, FilesService } from '../services/api';
import { Asset } from '../types/api';
import './AssetsPage.css';

// Move AssetForm outside to prevent recreation on every render
interface AssetFormProps {
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  title: string;
  formData: {
    name: string;
    description: string;
    type: string;
    url: string;
    file_id?: number;
  };
  setFormData: (data: any) => void;
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  uploading: boolean;
}

const AssetForm: React.FC<AssetFormProps> = React.memo(({ 
  onSubmit, 
  onCancel, 
  title, 
  formData, 
  setFormData, 
  selectedFile, 
  setSelectedFile, 
  uploading 
}) => {
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  }, [setSelectedFile]);

  const handleInputChange = useCallback((field: string, value: string) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  }, [setFormData]);

  return (
    <div className="asset-form-overlay">
      <div className="asset-form">
        <h3>{title}</h3>
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label htmlFor="name">Name:</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description:</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="type">Type:</label>
            <input
              type="text"
              id="type"
              value={formData.type}
              onChange={(e) => handleInputChange('type', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="file">File:</label>
            <input
              type="file"
              id="file"
              onChange={handleFileSelect}
              accept="*/*"
              required={!selectedFile && !title.includes('Edit')}
            />
            {selectedFile && (
              <div className="selected-file">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}
            {title.includes('Edit') && !selectedFile && (
              <div className="file-info">
                Current file will be preserved. Select a new file to replace it.
              </div>
            )}
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? 'Uploading...' : (title.includes('Edit') ? 'Update' : 'Create')}
            </button>
            <button type="button" onClick={onCancel} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
});

// Memoized asset card component
const AssetCard: React.FC<{
  asset: Asset;
  onEdit: (asset: Asset) => void;
  onDownload: (asset: Asset) => void;
  onDelete: (id: string) => void;
}> = React.memo(({ asset, onEdit, onDownload, onDelete }) => {
  const handleImageError = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik04MCAxMDBDODAgODkuNTQ0NyA4OC4wMDAxIDgxIDEwMCA4MUMxMTEuMDQ2IDgxIDEyMCA4OS41NDQ3IDEyMCAxMDBDMTIwIDExMC40NTUgMTExLjA0NiAxMTkgMTAwIDExOUM4OC4wMDAxIDExOSA4MCAxMTAuNDU1IDgwIDEwMFoiIGZpbGw9IiNDQ0NDQ0MiLz4KPC9zdmc+';
  }, []);

  const formattedDate = useMemo(() => {
    return new Date(asset.created_at).toLocaleDateString();
  }, [asset.created_at]);

  return (
    <div className="asset-card">
      <div className="asset-image">
        <img 
          src={asset.url} 
          alt={asset.name} 
          onError={handleImageError}
          loading="lazy"
        />
      </div>
      <div className="asset-info">
        <h3>{asset.name}</h3>
        <p className="asset-description">{asset.description}</p>
        <div className="asset-meta">
          <span className="asset-type">{asset.type}</span>
          <span className="asset-date">{formattedDate}</span>
          {asset.file_id && (
            <span className="asset-file">File ID: {asset.file_id}</span>
          )}
        </div>
        <div className="asset-actions">
          <button
            onClick={() => onEdit(asset)}
            className="btn-secondary btn-small"
          >
            Edit
          </button>
          <button
            onClick={() => onDownload(asset)}
            className="btn-primary btn-small"
          >
            Download
          </button>
          <button
            onClick={() => onDelete(asset.id)}
            className="btn-danger btn-small"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
});

const AssetsPage: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: '',
    url: '',
    file_id: undefined as number | undefined
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await AssetsService.getAssets(page, 12, searchQuery);
      setAssets(response.assets);
      setTotalPages(Math.ceil(response.total / 12));
    } catch (err) {
      setError('Failed to load assets. Please try again.');
      console.error('Load assets error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery]);

  // Debounced search effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1); // Reset to first page when searching
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load assets when page or search changes
  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  const handleCreateAsset = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // First upload the file
      const uploadedFile = await FilesService.uploadFile(selectedFile);
      
      // Then create the asset with the file_id
      const assetData = {
        ...formData,
        file_id: uploadedFile.id,
        url: uploadedFile.original_filename // Use filename as URL for now
      };
      
      await AssetsService.createAsset(assetData);
      setShowCreateForm(false);
      setFormData({ name: '', description: '', type: '', url: '', file_id: undefined });
      setSelectedFile(null);
      loadAssets();
    } catch (err) {
      setError('Failed to create asset. Please try again.');
      console.error('Create asset error:', err);
    } finally {
      setUploading(false);
    }
  }, [formData, selectedFile, loadAssets]);

  const handleUpdateAsset = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!editingAsset) return;

    setUploading(true);
    setError(null);

    try {
      let updatedAssetData = { ...formData };

      // If a new file is selected, upload it first
      if (selectedFile) {
        const uploadedFile = await FilesService.uploadFile(selectedFile);
        updatedAssetData = {
          ...updatedAssetData,
          file_id: uploadedFile.id,
          url: uploadedFile.original_filename
        };
      }

      await AssetsService.updateAsset(editingAsset.id, updatedAssetData);
      setEditingAsset(null);
      setFormData({ name: '', description: '', type: '', url: '', file_id: undefined });
      setSelectedFile(null);
      loadAssets();
    } catch (err) {
      setError('Failed to update asset. Please try again.');
      console.error('Update asset error:', err);
    } finally {
      setUploading(false);
    }
  }, [editingAsset, formData, selectedFile, loadAssets]);

  const handleDeleteAsset = useCallback(async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this asset?')) {
      return;
    }

    try {
      await AssetsService.deleteAsset(id);
      loadAssets();
    } catch (err) {
      setError('Failed to delete asset. Please try again.');
      console.error('Delete asset error:', err);
    }
  }, [loadAssets]);

  const handleDownloadAsset = useCallback(async (asset: Asset) => {
    try {
      // If the asset has a file_id, download from the files service
      if (asset.file_id) {
        const response = await fetch(`/api/files/${asset.file_id}/download`);
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = asset.name || 'asset-file';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          setError('Failed to download file. Please try again.');
        }
      } else if (asset.url) {
        // If no file_id but has URL, download from URL
        const a = document.createElement('a');
        a.href = asset.url;
        a.download = asset.name || 'asset-file';
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        setError('No file available for download.');
      }
    } catch (err) {
      setError('Failed to download asset. Please try again.');
      console.error('Download asset error:', err);
    }
  }, []);

  const startEdit = useCallback((asset: Asset) => {
    setEditingAsset(asset);
    setFormData({
      name: asset.name,
      description: asset.description || '',
      type: asset.type,
      url: asset.url,
      file_id: asset.file_id
    });
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingAsset(null);
    setFormData({ name: '', description: '', type: '', url: '', file_id: undefined });
    setSelectedFile(null);
  }, []);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handleShowCreateForm = useCallback(() => {
    setShowCreateForm(true);
  }, []);

  const handleHideCreateForm = useCallback(() => {
    setShowCreateForm(false);
  }, []);

  // Memoize the assets grid to prevent unnecessary re-renders
  const assetsGrid = useMemo(() => (
    <div className="assets-grid">
      {assets.map((asset) => (
        <AssetCard
          key={asset.id}
          asset={asset}
          onEdit={startEdit}
          onDownload={handleDownloadAsset}
          onDelete={handleDeleteAsset}
        />
      ))}
    </div>
  ), [assets, startEdit, handleDownloadAsset, handleDeleteAsset]);

  return (
    <div className="assets-page">
      <div className="assets-header">
        <div className="assets-header-left">
          <h2>Assets</h2>
          <div className="search-container">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search assets..."
              className="search-input"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="clear-search-btn"
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>
        </div>
        <button
          onClick={handleShowCreateForm}
          className="btn-primary"
        >
          Add Asset
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading assets...</div>
      ) : (
        <>
          {assetsGrid}

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
                className="btn-secondary"
              >
                Previous
              </button>
              <span className="page-info">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages}
                className="btn-secondary"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showCreateForm && (
        <AssetForm
          onSubmit={handleCreateAsset}
          onCancel={handleHideCreateForm}
          title="Create New Asset"
          formData={formData}
          setFormData={setFormData}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
          uploading={uploading}
        />
      )}

      {editingAsset && (
        <AssetForm
          onSubmit={handleUpdateAsset}
          onCancel={cancelEdit}
          title="Edit Asset"
          formData={formData}
          setFormData={setFormData}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
          uploading={uploading}
        />
      )}
    </div>
  );
};

export default AssetsPage; 