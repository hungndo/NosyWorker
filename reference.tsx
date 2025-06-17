"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Mail, MessageSquare, Plus, Edit3, Users, BarChart3 } from "lucide-react"
import { SummaryConfigDialog } from "./components/summary-config-dialog"
import { ChannelProfileDialog } from "./components/channel-profile-dialog"

interface Channel {
  id: string
  name: string
  type: "outlook" | "slack"
  enabled: boolean
  profile?: {
    audience: string
    dataSources: string[]
  }
}

export default function NosyWorkerDashboard() {
  const [channels, setChannels] = useState<Channel[]>([
    {
      id: "1",
      name: "Customer Support",
      type: "slack",
      enabled: true,
      profile: {
        audience: "Customer Success Team",
        dataSources: ["Support Tickets", "Usage Analytics"],
      },
    },
    {
      id: "2",
      name: "sales@company.com",
      type: "outlook",
      enabled: true,
      profile: {
        audience: "Sales Team",
        dataSources: ["CRM Data", "Lead Scores"],
      },
    },
    {
      id: "3",
      name: "Engineering Updates",
      type: "slack",
      enabled: false,
    },
    {
      id: "4",
      name: "team@company.com",
      type: "outlook",
      enabled: true,
    },
  ])

  const [summaryConfigOpen, setSummaryConfigOpen] = useState(false)
  const [channelProfileOpen, setChannelProfileOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null)

  const toggleChannel = (channelId: string) => {
    setChannels(
      channels.map((channel) => (channel.id === channelId ? { ...channel, enabled: !channel.enabled } : channel)),
    )
  }

  const openChannelProfile = (channel: Channel) => {
    setSelectedChannel(channel)
    setChannelProfileOpen(true)
  }

  const updateChannelProfile = (channelId: string, profile: { audience: string; dataSources: string[] }) => {
    setChannels(channels.map((channel) => (channel.id === channelId ? { ...channel, profile } : channel)))
  }

  const enabledChannels = channels.filter((channel) => channel.enabled)

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">NosyWorker Dashboard</h1>
            <p className="text-gray-600 mt-1">Your Intelligent Operations Assistant</p>
          </div>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Channels</p>
                  <p className="text-2xl font-bold">{enabledChannels.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <MessageSquare className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Messages Processed</p>
                  <p className="text-2xl font-bold">1,247</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Actions Generated</p>
                  <p className="text-2xl font-bold">23</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Channel Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Communication Channels</CardTitle>
                <CardDescription>
                  Select which Outlook emails and Slack channels to monitor and summarize
                </CardDescription>
              </div>
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Channel
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {channels.map((channel) => (
                <div key={channel.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3">
                      {channel.type === "outlook" ? (
                        <Mail className="h-5 w-5 text-blue-600" />
                      ) : (
                        <MessageSquare className="h-5 w-5 text-green-600" />
                      )}
                      <div>
                        <p className="font-medium">{channel.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={channel.type === "outlook" ? "default" : "secondary"}>
                            {channel.type === "outlook" ? "Outlook" : "Slack"}
                          </Badge>
                          {channel.profile && (
                            <Badge variant="outline" className="text-xs">
                              Profile Configured
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openChannelProfile(channel)}
                      className="flex items-center gap-2"
                    >
                      <Edit3 className="h-4 w-4" />
                      {channel.profile ? "Edit Profile" : "Set Profile"}
                    </Button>
                    <Switch checked={channel.enabled} onCheckedChange={() => toggleChannel(channel.id)} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest summaries and actions from your channels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                <MessageSquare className="h-5 w-5 text-green-600 mt-1" />
                <div className="flex-1">
                  <p className="font-medium">Customer Support Summary</p>
                  <p className="text-sm text-gray-600 mt-1">
                    3 new support tickets requiring attention. 2 customers reporting login issues.
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline">Action Required</Badge>
                    <span className="text-xs text-gray-500">2 minutes ago</span>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                <Mail className="h-5 w-5 text-blue-600 mt-1" />
                <div className="flex-1">
                  <p className="font-medium">Sales Team Update</p>
                  <p className="text-sm text-gray-600 mt-1">
                    New lead from enterprise client. Follow-up meeting scheduled for tomorrow.
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary">Informational</Badge>
                    <span className="text-xs text-gray-500">15 minutes ago</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <SummaryConfigDialog open={summaryConfigOpen} onOpenChange={setSummaryConfigOpen} />

      <ChannelProfileDialog
        open={channelProfileOpen}
        onOpenChange={setChannelProfileOpen}
        channel={selectedChannel}
        onSave={updateChannelProfile}
      />
    </div>
  )
}
