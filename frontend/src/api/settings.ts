import { apiClient } from './client';

export interface LLMProviderInfo {
  active_provider: string;
  display_name: string;
  policy_url: string;
  privacy_notice: string;
  is_third_party: boolean;
}

export async function getLLMProviderInfo(): Promise<LLMProviderInfo> {
  return apiClient<LLMProviderInfo>('/api/v1/settings/llm-provider');
}
