import { NotImplementedError } from './base'

interface ProfileData {
  name: string
  email: string
  avatar?: string
}

interface AiConfig {
  model: string
  temperature: number
  maxTokens: number
}

interface AppearanceConfig {
  theme: 'light' | 'dark' | 'system'
  fontSize: 'small' | 'medium' | 'large'
}

export const SettingsService = {
  async getProfile(): Promise<ProfileData> {
    throw new NotImplementedError('SettingsService', 'getProfile')
  },

  async updateProfile(_data: Partial<ProfileData>): Promise<ProfileData> {
    throw new NotImplementedError('SettingsService', 'updateProfile')
  },

  async getAiConfig(): Promise<AiConfig> {
    throw new NotImplementedError('SettingsService', 'getAiConfig')
  },

  async updateAiConfig(_config: Partial<AiConfig>): Promise<AiConfig> {
    throw new NotImplementedError('SettingsService', 'updateAiConfig')
  },

  async getAppearance(): Promise<AppearanceConfig> {
    throw new NotImplementedError('SettingsService', 'getAppearance')
  },

  async updateAppearance(
    _config: Partial<AppearanceConfig>
  ): Promise<AppearanceConfig> {
    throw new NotImplementedError('SettingsService', 'updateAppearance')
  },
}
