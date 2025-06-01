import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Divider
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import YouTubeIcon from '@mui/icons-material/YouTube';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    notification_time: '09:00'
  });
  const [channels, setChannels] = useState([
    { youtube_channel_url: '', channel_name: '' }
  ]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleChannelChange = (index, field, value) => {
    const updatedChannels = [...channels];
    updatedChannels[index][field] = value;
    setChannels(updatedChannels);
  };

  const addChannel = () => {
    setChannels([...channels, { youtube_channel_url: '', channel_name: '' }]);
  };

  const removeChannel = (index) => {
    if (channels.length > 1) {
      const updatedChannels = channels.filter((_, i) => i !== index);
      setChannels(updatedChannels);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // 각 채널에 대해 개별적으로 구독 등록
      const promises = channels.map(channel => {
        const subscriptionData = {
          ...formData,
          youtube_channel_url: channel.youtube_channel_url,
          channel_name: channel.channel_name
        };
        return axios.post('http://localhost:8000/api/subscriptions/', subscriptionData);
      });

      await Promise.all(promises);
      
      setMessage({ 
        type: 'success', 
        text: `${channels.length}개 채널 구독이 성공적으로 등록되었습니다! 이메일을 확인해주세요.` 
      });
      
      // 3초 후 홈으로 이동
      setTimeout(() => {
        navigate('/');
      }, 3000);
      
    } catch (error) {
      console.log('Error response:', error.response);
      
      let errorMessage = '등록 중 오류가 발생했습니다.';
      
      if (error.response?.data) {
        // 이메일 중복 오류 체크
        if (error.response.data.error && error.response.data.error.includes('이미 등록된 이메일')) {
          errorMessage = `이미 등록된 이메일입니다. "${formData.email}"은 이미 사용 중입니다.`;
        }
        // 다른 필드 오류들 체크
        else if (error.response.data.email) {
          errorMessage = `이메일 오류: ${error.response.data.email[0]}`;
        }
        else if (error.response.data.youtube_channel_url) {
          errorMessage = `YouTube URL 오류: ${error.response.data.youtube_channel_url[0]}`;
        }
        else if (error.response.data.password) {
          errorMessage = `비밀번호 오류: ${error.response.data.password[0]}`;
        }
        else if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        }
        else if (error.response.data.error) {
          errorMessage = error.response.data.error;
        }
      }
      
      setMessage({ 
        type: 'error', 
        text: errorMessage
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
          <YouTubeIcon sx={{ fontSize: 48, color: 'red', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            YouTube 채널 구독 등록
          </Typography>
          <Typography variant="body1" color="text.secondary">
            좋아하는 YouTube 채널들의 새로운 영상 알림을 받아보세요
          </Typography>
        </Box>
      </Box>

      {/* 등록 폼 */}
      <Paper elevation={3} sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Box mb={3}>
            <TextField
              fullWidth
              label="이름"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              variant="outlined"
              helperText="알림 이메일에 표시될 이름입니다"
            />
          </Box>

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
              helperText="새로운 영상 알림을 받을 이메일 주소입니다"
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
              helperText="구독 정보 수정 시 사용할 비밀번호입니다 (최소 6자)"
              inputProps={{ minLength: 6 }}
            />
          </Box>

          <Box mb={3}>
            <FormControl fullWidth>
              <InputLabel>알림 시간</InputLabel>
              <Select
                name="notification_time"
                value={formData.notification_time}
                onChange={handleChange}
                label="알림 시간"
              >
                <MenuItem value="06:00">오전 6시</MenuItem>
                <MenuItem value="06:30">오전 6시 30분</MenuItem>
                <MenuItem value="07:00">오전 7시</MenuItem>
                <MenuItem value="07:30">오전 7시 30분</MenuItem>
                <MenuItem value="08:00">오전 8시</MenuItem>
                <MenuItem value="08:30">오전 8시 30분</MenuItem>
                <MenuItem value="09:00">오전 9시</MenuItem>
                <MenuItem value="09:30">오전 9시 30분</MenuItem>
                <MenuItem value="10:00">오전 10시</MenuItem>
                <MenuItem value="10:30">오전 10시 30분</MenuItem>
                <MenuItem value="11:00">오전 11시</MenuItem>
                <MenuItem value="11:30">오전 11시 30분</MenuItem>
                <MenuItem value="12:00">오후 12시</MenuItem>
                <MenuItem value="12:30">오후 12시 30분</MenuItem>
                <MenuItem value="13:00">오후 1시</MenuItem>
                <MenuItem value="13:30">오후 1시 30분</MenuItem>
                <MenuItem value="14:00">오후 2시</MenuItem>
                <MenuItem value="14:30">오후 2시 30분</MenuItem>
                <MenuItem value="15:00">오후 3시</MenuItem>
                <MenuItem value="15:30">오후 3시 30분</MenuItem>
                <MenuItem value="16:00">오후 4시</MenuItem>
                <MenuItem value="16:30">오후 4시 30분</MenuItem>
                <MenuItem value="17:00">오후 5시</MenuItem>
                <MenuItem value="17:30">오후 5시 30분</MenuItem>
                <MenuItem value="18:00">오후 6시</MenuItem>
                <MenuItem value="18:30">오후 6시 30분</MenuItem>
                <MenuItem value="19:00">오후 7시</MenuItem>
                <MenuItem value="19:30">오후 7시 30분</MenuItem>
                <MenuItem value="20:00">오후 8시</MenuItem>
                <MenuItem value="20:30">오후 8시 30분</MenuItem>
                <MenuItem value="21:00">오후 9시</MenuItem>
                <MenuItem value="21:30">오후 9시 30분</MenuItem>
                <MenuItem value="22:00">오후 10시</MenuItem>
                <MenuItem value="22:30">오후 10시 30분</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* 채널 목록 */}
          <Typography variant="h6" gutterBottom>
            구독할 YouTube 채널들
          </Typography>
          
          {channels.map((channel, index) => (
            <Box key={index} mb={3} sx={{ border: '1px solid #e0e0e0', borderRadius: 2, p: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle1">
                  채널 {index + 1}
                </Typography>
                {channels.length > 1 && (
                  <IconButton 
                    onClick={() => removeChannel(index)}
                    color="error"
                    size="small"
                  >
                    <DeleteIcon />
                  </IconButton>
                )}
              </Box>
              
              <Box mb={2}>
                <TextField
                  fullWidth
                  label="YouTube 채널 URL"
                  value={channel.youtube_channel_url}
                  onChange={(e) => handleChannelChange(index, 'youtube_channel_url', e.target.value)}
                  required
                  variant="outlined"
                  placeholder="https://www.youtube.com/@channelname"
                  helperText="구독하고 싶은 YouTube 채널의 URL을 입력해주세요"
                />
              </Box>

              <Box>
                <TextField
                  fullWidth
                  label="채널 이름"
                  value={channel.channel_name}
                  onChange={(e) => handleChannelChange(index, 'channel_name', e.target.value)}
                  required
                  variant="outlined"
                  helperText="YouTube 채널의 이름을 입력해주세요"
                />
              </Box>
            </Box>
          ))}

          <Box textAlign="center" mb={3}>
            <Button
              startIcon={<AddIcon />}
              onClick={addChannel}
              variant="outlined"
              color="primary"
            >
              채널 추가
            </Button>
          </Box>

          {message.text && (
            <Box mb={3}>
              <Alert severity={message.type}>
                {message.text}
              </Alert>
            </Box>
          )}

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
                  등록 중...
                </>
              ) : (
                `${channels.length}개 채널 구독 등록하기`
              )}
            </Button>
          </Box>
        </form>
      </Paper>

      {/* 안내 사항 */}
      <Box mt={4}>
        <Paper elevation={1} sx={{ p: 3, backgroundColor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            📋 이용 안내
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 여러 YouTube 채널을 한 번에 구독할 수 있습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 등록된 이메일 주소로 확인 메일이 발송됩니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 새로운 영상이 업로드되면 설정한 시간에 알림을 받습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • 언제든지 구독을 수정하거나 취소할 수 있습니다
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • 문의사항이 있으시면 관리자에게 연락해주세요
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default RegisterPage; 