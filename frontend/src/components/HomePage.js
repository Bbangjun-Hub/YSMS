import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Paper
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import EmailIcon from '@mui/icons-material/Email';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LoginIcon from '@mui/icons-material/Login';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* 헤더 섹션 */}
      <Box textAlign="center" mb={6}>
        <EmailIcon sx={{ fontSize: 60, color: 'red', mb: 2 }} />
        <Typography variant="h3" component="h1" gutterBottom>
          YouTube Summary Mailing Service
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          좋아하는 YouTube 채널의 새로운 영상을 이메일로 받아보세요
        </Typography>
      </Box>

      {/* 메인 액션 카드들 */}
      <Box sx={{ maxWidth: '1200px', mx: 'auto', mb: 8 }}>
        <Grid container spacing={3} justifyContent="center">
          <Grid item xs={12} md={4} lg={4}>
            <Card 
              sx={{ 
                height: 280,
                width: 350,
                mx: 'auto',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => navigate('/register')}
            >
              <CardContent sx={{ 
                textAlign: 'center', 
                p: 3,
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <PersonAddIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h5" component="h2" gutterBottom>
                    구독 등록
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: '40px' }}>
                    새로운 YouTube 채널을 구독하고 알림을 받아보세요
                  </Typography>
                </Box>
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={<PersonAddIcon />}
                  fullWidth
                >
                  등록하기
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4} lg={4}>
            <Card 
              sx={{ 
                height: 280,
                width: 350,
                mx: 'auto',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => navigate('/login')}
            >
              <CardContent sx={{ 
                textAlign: 'center', 
                p: 3,
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <LoginIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
                  <Typography variant="h5" component="h2" gutterBottom>
                    구독 관리
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: '40px' }}>
                    기존 구독을 수정하거나 삭제할 수 있습니다
                  </Typography>
                </Box>
                <Button 
                  variant="outlined" 
                  size="large"
                  startIcon={<LoginIcon />}
                  fullWidth
                >
                  로그인
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4} lg={4}>
            <Card 
              sx={{ 
                height: 280,
                width: 350,
                mx: 'auto',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => navigate('/admin-login')}
            >
              <CardContent sx={{ 
                textAlign: 'center', 
                p: 3,
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <Box>
                  <AdminPanelSettingsIcon sx={{ fontSize: 48, color: 'warning.main', mb: 2 }} />
                  <Typography variant="h5" component="h2" gutterBottom>
                    관리자 페이지
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: '40px' }}>
                    전체 구독 현황과 시스템을 관리합니다
                  </Typography>
                </Box>
                <Button 
                  variant="outlined" 
                  color="warning"
                  size="large"
                  startIcon={<AdminPanelSettingsIcon />}
                  fullWidth
                >
                  관리자
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* 서비스 설명 섹션 */}
      <Box sx={{ maxWidth: '1200px', mx: 'auto' }}>
        <Paper elevation={2} sx={{ p: 6, backgroundColor: 'grey.50' }}>
          <Typography variant="h4" component="h2" textAlign="center" gutterBottom sx={{ mb: 6 }}>
            서비스 특징
          </Typography>
          
          <Box sx={{ maxWidth: '600px', mx: 'auto' }}>
            {/* 정확한 알림 */}
            <Box sx={{ mb: 4, textAlign: 'center' }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: '1.5rem', mb: 2, fontWeight: 600 }}>
                🎯 정확한 알림
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6, fontSize: '1.1rem' }}>
                YouTube 채널의 최신 영상을 시간에 맞춰 내용을 정리하여 이메일로 발송합니다
              </Typography>
            </Box>

            {/* 맞춤 스케줄 */}
            <Box sx={{ mb: 4, textAlign: 'center' }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: '1.5rem', mb: 2, fontWeight: 600 }}>
                ⏰ 맞춤 스케줄
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6, fontSize: '1.1rem' }}>
                원하는 시간에 맞춰 이메일 알림을 받을 수 있습니다
              </Typography>
            </Box>

            {/* 간편한 관리 */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: '1.5rem', mb: 2, fontWeight: 600 }}>
                📱 간편한 관리
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6, fontSize: '1.1rem' }}>
                언제든지 구독을 추가, 수정, 삭제할 수 있습니다
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default HomePage; 