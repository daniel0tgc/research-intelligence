// Paper node constraints
CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT entity_name_type_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;

// Indexes for common lookups
CREATE INDEX paper_arxiv_id IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year);
CREATE INDEX paper_community IF NOT EXISTS FOR (p:Paper) ON (p.community_id);
