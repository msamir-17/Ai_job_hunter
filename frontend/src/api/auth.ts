import { apiClient } from './client';
import { AuthResponse, LoginPayload, RegisterPayload, User } from '../types/auth';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getStoredUser(): User | null {
  const data = localStorage.getItem(USER_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function removeAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function loginApi(payload: LoginPayload): Promise<AuthResponse> {
  const response = await apiClient<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setToken(response.access_token);
  setStoredUser(response.user);
  return response;
}

export async function registerApi(payload: RegisterPayload): Promise<AuthResponse> {
  const response = await apiClient<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setToken(response.access_token);
  setStoredUser(response.user);
  return response;
}

export async function getMeApi(): Promise<User> {
  const user = await apiClient<User>('/api/v1/auth/me', {
    method: 'GET',
  });
  setStoredUser(user);
  return user;
}

export async function deleteAccountApi(): Promise<void> {
  await apiClient<void>('/api/v1/auth/me', {
    method: 'DELETE',
  });
  removeAuth();
}
