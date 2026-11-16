-- Which dashboard a recipient belongs to. NULL = dental clinics (/admin), 'vet' = veterinarians (/admin/vet).
ALTER TABLE recipients ADD COLUMN segment TEXT;
