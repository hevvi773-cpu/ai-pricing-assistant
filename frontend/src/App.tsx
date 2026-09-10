import { BrowserRouter, Routes, Route } from 'react-router-dom'
import PricingPage from './pages/PricingPage/PricingPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PricingPage />} />
      </Routes>
    </BrowserRouter>
  )
}
