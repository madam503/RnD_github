#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <wiringPi.h>
#include <wiringPiSPI.h>

#define SCE				22
#define spi_chn0		0
#define SPEED_1MHz		1000000
#define SPI_MODE3		3
#define OBJECT			0xA0
#define SENSOR			0xA1

int16_t iSensor, iObject;
int16_t SPI_COMMAND(uint8_t ADR)
{
	uint8_t Data_Buf[3];
	
	Data_Buf[0] = ADR;
	Data_Buf[1] = 0x22;
	Data_Buf[2] = 0x22;
	
	digitalWrite(SCE, 0);
	delayMicroseconds(10);
	
	wiringPiSPIDataRW (spi_chn0, Data_Buf, 1);
	delayMicroseconds(10);
	wiringPiSPIDataRW (spi_chn0, Data_Buf+1, 1);
	delayMicroseconds(10);
	wiringPiSPIDataRW (spi_chn0, Data_Buf+2, 1);
	delayMicroseconds(10);
	
	digitalWrite(SCE, 1);
	return (Data_Buf[2]*256+Data_Buf[1]);
}

int main(void)
{
	wiringPiSetup();
	if(wiringPiSetupGpio() == -1)
	return 1;
	pinMode(SCE, OUTPUT);
	digitalWrite(SCE, 1);
	
	wiringPiSPISetupMode(spi_chn0, SPEED_1MHz, SPI_MODE3);
	delay(500);
	while(1)
	{
		iSensor = SPI_COMMAND(SENSOR);
		delayMicroseconds(10);
		iObject = SPI_COMMAND(OBJECT);
		delay(500);
		printf("Sensor : %5.1f , Object : %5.1f \n", (double)iSensor/10, (double)iObject/10);
	}
	return 0;
}
