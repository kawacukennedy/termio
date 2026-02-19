//! Knowledge graph model
//!
//! Graph-based knowledge representation with nodes and edges.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// A node in the knowledge graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeNode {
    /// Unique node ID
    pub id: Uuid,
    /// Node label/name
    pub label: String,
    /// Node type (e.g., "concept", "entity", "topic")
    pub node_type: String,
    /// Properties as key-value pairs
    pub properties: serde_json::Value,
    /// Optional embedding vector for semantic search
    #[serde(skip_serializing_if = "Option::is_none")]
    pub embedding: Option<Vec<f32>>,
    /// User who owns this node
    pub user_id: Uuid,
    /// When the node was created
    pub created_at: DateTime<Utc>,
    /// When the node was last updated
    pub updated_at: DateTime<Utc>,
}

impl KnowledgeNode {
    /// Create a new knowledge node
    pub fn new(
        label: impl Into<String>,
        node_type: impl Into<String>,
        user_id: Uuid,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            label: label.into(),
            node_type: node_type.into(),
            properties: serde_json::Value::Object(serde_json::Map::new()),
            embedding: None,
            user_id,
            created_at: now,
            updated_at: now,
        }
    }

    /// Set a property on the node
    pub fn with_property(mut self, key: impl Into<String>, value: serde_json::Value) -> Self {
        if let serde_json::Value::Object(ref mut map) = self.properties {
            map.insert(key.into(), value);
        }
        self
    }

    /// Set the embedding vector
    pub fn with_embedding(mut self, embedding: Vec<f32>) -> Self {
        self.embedding = Some(embedding);
        self
    }
}

/// Relationship type for edges
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeEdge {
    /// Unique edge ID
    pub id: Uuid,
    /// Source node ID
    pub source: Uuid,
    /// Target node ID
    pub target: Uuid,
    /// Relationship type (e.g., "related_to", "part_of", "derived_from")
    pub relation: String,
    /// Weight/strength of the relationship (0.0 - 1.0)
    pub weight: f32,
    /// Additional properties
    pub properties: serde_json::Value,
    /// When the edge was created
    pub created_at: DateTime<Utc>,
}

impl KnowledgeEdge {
    /// Create a new edge
    pub fn new(
        source: Uuid,
        target: Uuid,
        relation: impl Into<String>,
        weight: f32,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            source,
            target,
            relation: relation.into(),
            weight: weight.clamp(0.0, 1.0),
            properties: serde_json::Value::Object(serde_json::Map::new()),
            created_at: Utc::now(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_knowledge_node() {
        let user = Uuid::new_v4();
        let node = KnowledgeNode::new("Rust", "language", user)
            .with_property("paradigm", serde_json::json!("systems"));

        assert_eq!(node.label, "Rust");
        assert_eq!(node.node_type, "language");
        assert_eq!(node.properties["paradigm"], "systems");
    }

    #[test]
    fn test_knowledge_edge() {
        let src = Uuid::new_v4();
        let tgt = Uuid::new_v4();
        let edge = KnowledgeEdge::new(src, tgt, "related_to", 0.8);

        assert_eq!(edge.source, src);
        assert_eq!(edge.target, tgt);
        assert_eq!(edge.weight, 0.8);
    }
}
