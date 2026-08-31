import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const client = axios.create({ baseURL });

export const getBrands = () => client.get("/brands").then((r) => r.data.brands);

export const getDailyStats = (brand) =>
  client.get(`/daily-stats/${encodeURIComponent(brand)}`).then((r) => r.data);

export const getTopics = (brand) =>
  client.get(`/topics/${encodeURIComponent(brand)}`).then((r) => r.data);

export const getMentions = (brand, date) =>
  client
    .get(`/mentions/${encodeURIComponent(brand)}`, { params: { limit: 200, ...(date ? { date } : {}) } })
    .then((r) => r.data);
