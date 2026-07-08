'use client'

import { useState } from 'react'
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
} from 'lucide-react'

const settingsSections = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'appearance', label: 'Appearance', icon: Palette },
]

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('profile')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-surface-900">
          Settings
        </h1>
        <p className="mt-1 text-sm text-surface-500">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Settings Navigation */}
        <nav className="w-full shrink-0 space-y-1 lg:w-56">
          {settingsSections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors ${
                activeSection === section.id
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
              }`}
            >
              <section.icon className="h-4 w-4" />
              {section.label}
            </button>
          ))}
        </nav>

        {/* Settings Content */}
        <div className="flex-1">
          <div className="card">
            {activeSection === 'profile' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-surface-900">
                    Profile Information
                  </h3>
                  <p className="mt-1 text-sm text-surface-500">
                    Update your personal details
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-xl font-bold text-primary-700">
                    JD
                  </div>
                  <div>
                    <button className="btn-secondary text-sm">
                      Change Avatar
                    </button>
                  </div>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      First Name
                    </label>
                    <input
                      type="text"
                      className="input-field"
                      defaultValue="John"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      Last Name
                    </label>
                    <input
                      type="text"
                      className="input-field"
                      defaultValue="Doe"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      Email
                    </label>
                    <input
                      type="email"
                      className="input-field"
                      defaultValue="john@company.com"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      Bio
                    </label>
                    <textarea
                      className="input-field min-h-[100px]"
                      defaultValue="Product manager with a passion for data-driven insights."
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 border-t border-surface-200 pt-6">
                  <button className="btn-secondary">Cancel</button>
                  <button className="btn-primary">Save Changes</button>
                </div>
              </div>
            )}

            {activeSection === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-surface-900">
                    Notification Preferences
                  </h3>
                  <p className="mt-1 text-sm text-surface-500">
                    Choose what notifications you receive
                  </p>
                </div>

                <div className="space-y-4">
                  {[
                    {
                      title: 'Analysis Complete',
                      description:
                        'Get notified when a document analysis finishes',
                    },
                    {
                      title: 'Document Shared',
                      description:
                        'Receive a notification when someone shares a document with you',
                    },
                    {
                      title: 'Weekly Digest',
                      description:
                        'Get a weekly summary of your document activity',
                    },
                  ].map((item) => (
                    <div
                      key={item.title}
                      className="flex items-center justify-between rounded-lg border border-surface-200 p-4"
                    >
                      <div>
                        <p className="text-sm font-medium text-surface-900">
                          {item.title}
                        </p>
                        <p className="text-xs text-surface-500">
                          {item.description}
                        </p>
                      </div>
                      <label className="relative inline-flex cursor-pointer items-center">
                        <input
                          type="checkbox"
                          defaultChecked
                          className="peer sr-only"
                        />
                        <div className="h-6 w-11 rounded-full bg-surface-300 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary-600 peer-checked:after:translate-x-full" />
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeSection === 'security' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-surface-900">
                    Security Settings
                  </h3>
                  <p className="mt-1 text-sm text-surface-500">
                    Manage your password and security preferences
                  </p>
                </div>

                <div className="space-y-5">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      Current Password
                    </label>
                    <input
                      type="password"
                      className="input-field max-w-md"
                      placeholder="Enter current password"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      New Password
                    </label>
                    <input
                      type="password"
                      className="input-field max-w-md"
                      placeholder="Enter new password"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-surface-700">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      className="input-field max-w-md"
                      placeholder="Confirm new password"
                    />
                  </div>
                  <button className="btn-primary">Update Password</button>
                </div>

                <div className="border-t border-surface-200 pt-6">
                  <h4 className="text-sm font-semibold text-surface-900">
                    Two-Factor Authentication
                  </h4>
                  <p className="mt-1 text-sm text-surface-500">
                    Add an extra layer of security to your account
                  </p>
                  <button className="btn-secondary mt-4">
                    Enable 2FA
                  </button>
                </div>
              </div>
            )}

            {activeSection === 'appearance' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-surface-900">
                    Appearance
                  </h3>
                  <p className="mt-1 text-sm text-surface-500">
                    Customize how the application looks
                  </p>
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-surface-700">
                    Theme
                  </label>
                  <div className="flex gap-3">
                    {['Light', 'Dark', 'System'].map((theme) => (
                      <button
                        key={theme}
                        className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                          theme === 'Light'
                            ? 'border-primary-500 bg-primary-50 text-primary-700'
                            : 'border-surface-300 text-surface-600 hover:bg-surface-50'
                        }`}
                      >
                        {theme}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
