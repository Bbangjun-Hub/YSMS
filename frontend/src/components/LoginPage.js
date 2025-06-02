import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LoginIcon from '@mui/icons-material/Login';
import axios from 'axios';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.post('http://localhost:8000/api/subscriptions/login/', formData);
      
      if (response.data.user && response.data.subscriptions) {
        // 사용자 정보와 구독 정보를 로컬 스토리지에 저장
        localStorage.setItem('userEmail', formData.email);
        localStorage.setItem('subscriptionData', JSON.stringify({
          user: response.data.user,
          subscriptions: response.data.subscriptions
        }));
        // 간단한 인증 토큰 생성 (실제로는 백엔드에서 제공해야 함)
        localStorage.setItem('authToken', `user-${formData.email}-${Date.now()}`);
        
        const subscriptionCount = response.data.subscription_count || response.data.subscriptions.length;
        setMessage({ 
          type: 'success', 
          text: `로그인 성공! ${subscriptionCount}개의 구독을 관리할 수 있습니다. 구독 관리 페이지로 이동합니다.` 
        });
        
        // 2초 후 편집 페이지로 이동
        setTimeout(() => {
          navigate('/edit');
        }, 2000);
      }
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.non_field_errors?.[0] || 
              error.response?.data?.detail || 
              '로그인 중 오류가 발생했습니다.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      {/* 헤더 */}
      <Box mb={4}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mb: 2 }}
        >
          홈으로 돌아가기
        </Button>
        
        <Box textAlign="center">
          <LoginIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            구독 관리 로그인
          </Typography>
          <Typography variant="body1" color="text.secondary">
            구독 정보를 수정하려면 로그인하세요
          </Typography>
        </Box>
      </Box>

      {/* 로그인 폼 */}
      <Paper elevation={3} sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Box mb={3}>
            <TextField
              fullWidth
              label="이메일 주소"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              variant="outlined"
              helperText="구독 등록 시 사용한 이메일 주소를 입력해주세요"
              autoFocus
            />
          </Box>

          <Box mb={3}>
            <TextField
              fullWidth
              label="비밀번호"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              variant="outlined"
              helperText="구독 등록 시 설정한 비밀번호를 입력해주세요"
            />
          </Box>

          <Box textAlign="center">
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ minWidth: 200 }}
            >
              {loading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  로그인 중...
                </>
              ) : (
                '로그인'
              )}
            </Button>
          </Box>
        </form>

        {message.text && (
          <Box mt={3}>
            <Alert severity={message.type}>
              {message.text}
            </Alert>
          </Box>
        )}
      </Paper>

      {/* 안내 사항 */}
      <Box mt={4}>
        <Paper elevation={1} sx={{ p: 3, backgroundColor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            🔐 로그인 안내
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 구독 등록 시 사용한 이메일 주소와 비밀번호로 로그인할 수 있습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 로그인 후 구독 정보를 수정하거나 삭제할 수 있습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 비밀번호를 잊으셨다면 관리자에게 문의해주세요
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • 보안을 위해 세션은 일정 시간 후 자동으로 만료됩니다
          </Typography>
        </Paper>
      </Box>

      {/* 추가 액션 */}
      <Box mt={3} textAlign="center">
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          아직 구독하지 않으셨나요?
        </Typography>
        <Button
          variant="outlined"
          onClick={() => navigate('/register')}
        >
          새로 구독하기
        </Button>
        
        <Box mt={2}>
          <Button
            variant="text"
            color="warning"
            onClick={() => navigate('/admin-login')}
            size="small"
          >
            관리자 로그인
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default LoginPage; 