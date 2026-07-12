/**
 * Settings service — UI-only state for now.
 * No backend endpoints exist for profile / AI config / appearance yet.
 */

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
    return { name: 'Alex Chen', email: 'alex@projectlens.ai', avatar: undefined }
  },

  async updateProfile(data: Partial<ProfileData>): Promise<ProfileData> {
    return {
      name: data.name ?? 'Alex Chen',
      email: data.email ?? 'alex@projectlens.ai',
      avatar: data.avatar,
    }
  },

  async getAiConfig(): Promise<AiConfig> {
    return { model: 'gpt-4', temperature: 0.7, maxTokens: 4096 }
  },

  async updateAiConfig(config: Partial<AiConfig>): Promise<AiConfig> {
    return {
      model: config.model ?? 'gpt-4',
      temperature: config.temperature ?? 0.7,
      maxTokens: config.maxTokens ?? 4096,
    }
  },

  async getAppearance(): Promise<AppearanceConfig> {
    return { theme: 'dark', fontSize: 'medium' }
  },

  async updateAppearance(config: Partial<AppearanceConfig>): Promise<AppearanceConfig> {
    return {
      theme: config.theme ?? 'dark',
      fontSize: config.fontSize ?? 'medium',
    }
  },
}
