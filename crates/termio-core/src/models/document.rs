//! Document model
//!
//! Uploaded document processing with status tracking.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Document processing status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DocumentStatus {
    /// Waiting to be processed
    Pending,
    /// Currently being processed
    Processing,
    /// Successfully indexed
    Indexed,
    /// Processing failed
    Failed,
}

/// Document type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DocumentType {
    /// Plain text
    Text,
    /// Markdown
    Markdown,
    /// PDF
    Pdf,
    /// Code file
    Code,
    /// Other format
    Other,
}

/// An uploaded document for processing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    /// Unique document ID
    pub id: Uuid,
    /// User who uploaded the document
    pub user_id: Uuid,
    /// Document name
    pub name: String,
    /// Document type
    pub doc_type: DocumentType,
    /// File size in bytes
    pub size_bytes: u64,
    /// Processing status
    pub status: DocumentStatus,
    /// Extracted text content (after processing)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    /// Number of chunks/sections
    pub chunk_count: u32,
    /// Error message if processing failed
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    /// When the document was uploaded
    pub created_at: DateTime<Utc>,
    /// When the document was last updated
    pub updated_at: DateTime<Utc>,
}

impl Document {
    /// Create a new pending document
    pub fn new(user_id: Uuid, name: impl Into<String>, doc_type: DocumentType, size_bytes: u64) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            user_id,
            name: name.into(),
            doc_type,
            size_bytes,
            status: DocumentStatus::Pending,
            content: None,
            chunk_count: 0,
            error: None,
            created_at: now,
            updated_at: now,
        }
    }

    /// Mark as processing
    pub fn start_processing(&mut self) {
        self.status = DocumentStatus::Processing;
        self.updated_at = Utc::now();
    }

    /// Mark as indexed with extracted content
    pub fn complete(&mut self, content: String, chunk_count: u32) {
        self.status = DocumentStatus::Indexed;
        self.content = Some(content);
        self.chunk_count = chunk_count;
        self.updated_at = Utc::now();
    }

    /// Mark as failed
    pub fn fail(&mut self, error: impl Into<String>) {
        self.status = DocumentStatus::Failed;
        self.error = Some(error.into());
        self.updated_at = Utc::now();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_document_lifecycle() {
        let user = Uuid::new_v4();
        let mut doc = Document::new(user, "test.md", DocumentType::Markdown, 1024);

        assert_eq!(doc.status, DocumentStatus::Pending);

        doc.start_processing();
        assert_eq!(doc.status, DocumentStatus::Processing);

        doc.complete("# Hello\nContent".to_string(), 2);
        assert_eq!(doc.status, DocumentStatus::Indexed);
        assert_eq!(doc.chunk_count, 2);
        assert!(doc.content.is_some());
    }

    #[test]
    fn test_document_failure() {
        let user = Uuid::new_v4();
        let mut doc = Document::new(user, "bad.pdf", DocumentType::Pdf, 2048);

        doc.start_processing();
        doc.fail("Parse error: invalid PDF");
        assert_eq!(doc.status, DocumentStatus::Failed);
        assert!(doc.error.is_some());
    }
}
