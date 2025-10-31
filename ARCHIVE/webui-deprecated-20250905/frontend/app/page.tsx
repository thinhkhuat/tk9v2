'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/use-toast'
import { 
  Search, 
  FileText, 
  Download, 
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  History,
  Settings,
  Globe,
  Brain
} from 'lucide-react'
import { useResearchStore } from '@/stores/research'
import { useAuthStore } from '@/stores/auth'
import ResearchProgress from '@/components/research/ResearchProgress'
import ResearchHistory from '@/components/research/ResearchHistory'

export default function Dashboard() {
  const { toast } = useToast()
  const { user } = useAuthStore()
  const { 
    currentSession, 
    isConnected, 
    startResearch,
    isLoading 
  } = useResearchStore()
  
  const [query, setQuery] = useState('')
  const [tone, setTone] = useState('objective')
  const [language, setLanguage] = useState('en')
  const [activeTab, setActiveTab] = useState('new')

  const handleStartResearch = async () => {
    if (!query.trim()) {
      toast({
        title: "Query Required",
        description: "Please enter a research question",
        variant: "destructive"
      })
      return
    }

    try {
      await startResearch({
        query: query.trim(),
        tone,
        language,
        task_config: {
          max_sections: 5,
          publish_formats: ['pdf', 'docx', 'markdown']
        }
      })
      
      toast({
        title: "Research Started",
        description: "Your research task has been queued for processing"
      })
      
      // Switch to progress tab
      setActiveTab('progress')
      
      // Clear form
      setQuery('')
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to start research. Please try again.",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Deep Research Dashboard</h1>
        <p className="text-muted-foreground">
          Transform any question into comprehensive research with AI agents
        </p>
        <div className="flex items-center gap-2 mt-4">
          <Badge variant={isConnected ? "default" : "destructive"}>
            <Activity className="h-3 w-3 mr-1" />
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          <Badge variant="outline">
            <Brain className="h-3 w-3 mr-1" />
            9 AI Agents
          </Badge>
          <Badge variant="outline">
            <Globe className="h-3 w-3 mr-1" />
            50+ Languages
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="new">
            <Search className="h-4 w-4 mr-2" />
            New Research
          </TabsTrigger>
          <TabsTrigger value="progress">
            <Activity className="h-4 w-4 mr-2" />
            Progress
          </TabsTrigger>
          <TabsTrigger value="history">
            <History className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="new">
          <Card>
            <CardHeader>
              <CardTitle>Start New Research</CardTitle>
              <CardDescription>
                Enter your research question and configure options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="query">Research Question</Label>
                <Textarea
                  id="query"
                  placeholder="What would you like to research today?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="min-h-[100px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tone">Research Tone</Label>
                  <Select value={tone} onValueChange={setTone}>
                    <SelectTrigger id="tone">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="objective">Objective</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="optimistic">Optimistic</SelectItem>
                      <SelectItem value="balanced">Balanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Output Language</Label>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger id="language">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="vi">Vietnamese</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="zh">Chinese</SelectItem>
                      <SelectItem value="ja">Japanese</SelectItem>
                      <SelectItem value="ko">Korean</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="text-sm text-muted-foreground">
                  Estimated time: 3-5 minutes
                </div>
                <Button 
                  onClick={handleStartResearch}
                  disabled={isLoading || !query.trim()}
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-4 w-4" />
                      Start Research
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="progress">
          {currentSession ? (
            <ResearchProgress sessionId={currentSession.id} />
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  No active research session. Start a new research to see progress.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <ResearchHistory />
        </TabsContent>
      </Tabs>
    </div>
  )
}