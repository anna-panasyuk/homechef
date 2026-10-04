import { getMeals, cooks, locations } from '../data/catalog.js';
// Replace with a PostgreSQL/Supabase adapter when real listings are added.
export const catalogRepository = { async getCatalog() { return {meals:getMeals(),cooks,locations}; } };
