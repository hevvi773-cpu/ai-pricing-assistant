import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sparkles, Tag, Upload, MessageSquare, RefreshCw, CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Toaster, toast } from 'sonner'
import { pricingService, type PricingResult, type AdjustRequest } from '@/services/pricingService'

const CONDITIONS = ['全新', '几乎全新', '轻微使用痕迹', '有明显使用痕迹']
const CATEGORIES = ['手机数码', '电脑平板', '教材书籍', '生活用品', '服饰鞋包', '运动户外', '其他']

export default function PricingPage() {
  const [productName, setProductName] = useState('')
  const [category, setCategory] = useState('')
  const [condition, setCondition] = useState('几乎全新')
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PricingResult | null>(null)
  const [adjustMessage, setAdjustMessage] = useState('')
  const [adjustLoading, setAdjustLoading] = useState(false)

  const handleSubmit = async () => {
    if (!productName.trim()) return
    setLoading(true)
    try {
      const res = await pricingService.getPrice({
        product_name: productName,
        category,
        condition,
      })
      setResult(res)
    } catch (e) {
      console.error(e)
      toast.error('估价失败，请检查网络后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleAdjust = async () => {
    if (!adjustMessage.trim() || !result) return
    setAdjustLoading(true)
    try {
      const req: AdjustRequest = {
        product_name: productName,
        category,
        condition,
        current_price: result.suggested_price,
        message: adjustMessage,
      }
      const res = await pricingService.adjustPrice(req)
      setResult(res)
      setAdjustMessage('')
      toast.success('价格已调整')
    } catch (e) {
      console.error(e)
      toast.error('调整失败，请重试')
    } finally {
      setAdjustLoading(false)
    }
  }

  const getConfidenceColor = (level: string) => {
    if (level === 'high') return 'bg-green-100 text-green-800 border-green-200'
    if (level === 'medium') return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-gray-100 text-gray-600 border-gray-200'
  }

  const getConfidenceLabel = (level: string) => {
    if (level === 'high') return '高置信度 · 推荐'
    if (level === 'medium') return '中置信度 · 参考'
    return '低置信度 · 估算'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Toaster position="top-right" />
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Tag className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AI 定价助手</h1>
            <p className="text-sm text-gray-500">二手商品智能估价 · AI-Native</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <Card className="mb-6 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              输入商品信息
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>商品名称</Label>
              <Input
                placeholder="例如：iPhone 13 128G 蓝色"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>品类</Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择品类" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>成色</Label>
                <Select value={condition} onValueChange={setCondition}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONDITIONS.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>商品图片（可选）</Label>
              {imagePreview ? (
                <div className="relative inline-block">
                  <img src={imagePreview} alt="预览" className="w-32 h-32 object-cover rounded-lg border" />
                  <button
                    type="button"
                    onClick={() => { setImage(null); setImagePreview(null); if (fileInputRef.current) fileInputRef.current.value = '' }}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div
                  className="border-2 border-dashed rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500">点击或拖拽上传图片</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        setImage(file)
                        setImagePreview(URL.createObjectURL(file))
                      }
                    }}
                  />
                </div>
              )}
            </div>
            <Button
              className="w-full"
              size="lg"
              onClick={handleSubmit}
              disabled={loading || !productName.trim()}
            >
              {loading ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />AI 正在估价...</>
              ) : (
                <><Sparkles className="w-4 h-4 mr-2" />AI 智能估价</>
              )}
            </Button>
          </CardContent>
        </Card>

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <Card className="shadow-lg border-blue-100">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-blue-500" />
                      估价结果
                    </CardTitle>
                    <Badge className={getConfidenceColor(result.confidence)}>
                      {getConfidenceLabel(result.confidence)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="text-center py-4">
                    <p className="text-sm text-gray-500 mb-1">建议价格</p>
                    <p className="text-5xl font-bold text-blue-600">
                      ¥{result.suggested_price}
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                      区间：¥{result.price_min} ~ ¥{result.price_max}
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">最低价</span>
                      <span className="font-medium">¥{result.price_min}</span>
                      <span className="text-gray-500">最高价</span>
                      <span className="font-medium">¥{result.price_max}</span>
                    </div>
                    <Slider
                      defaultValue={[result.price_min, result.price_max]}
                      max={result.price_max * 1.5}
                      step={1}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-400 text-center">
                      拖动滑块微调价格，AI 会根据调整重新评估
                    </p>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                    <div className="flex items-start gap-2">
                      <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-blue-800 mb-1">AI 定价理由</p>
                        <p className="text-sm text-blue-700">{result.reasoning}</p>
                        {result.comparables && result.comparables.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-blue-200">
                            <p className="text-xs text-blue-600 mb-1">参考了 {result.comparables.length} 条同类成交记录</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {result.confidence === 'low' && (
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-gray-600">
                        数据源不足，价格区间已自动拉宽。本结果仅供参考，建议结合市场实际情况判断。
                      </p>
                    </div>
                  )}

                  <div className="space-y-3 pt-4 border-t">
                    <Label className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" />
                      对话式微调
                    </Label>
                    <Textarea
                      placeholder="例如：我急售，可以便宜点；这个配件很齐全，应该能贵点..."
                      value={adjustMessage}
                      onChange={(e) => setAdjustMessage(e.target.value)}
                      rows={2}
                    />
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={handleAdjust}
                      disabled={adjustLoading || !adjustMessage.trim()}
                    >
                      {adjustLoading ? (
                        <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />AI 调整中...</>
                      ) : (
                        <>发送调整请求</>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-8 text-center text-xs text-gray-400">
          <p>AI-Native 定价模块 · 基于 Mercari 公开数据集 + 大模型推理</p>
          <p className="mt-1">价格仅供参考，实际成交价以市场为准</p>
        </div>
      </main>
    </div>
  )
}
