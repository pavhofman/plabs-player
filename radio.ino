#include <TFT_ST7735.h> // Graphics and font library for ST7735 driver chip
#include <SPI.h>

TFT_ST7735 tft = TFT_ST7735();  // Invoke library, pins defined in User_Setup.h

// period in ms to check volume value (and send over serial if change detected)
#define VOLUME_CHECK_PERIOD 100

// first byte of incoming frame
#define FRAME_START 254
// last byte of incoming frame
#define FRAME_END 253

// time limit in millis for reception of the whole screen structure
// is used to skip corrupted incoming data
#define SERIAL_TIMEOUT 500

// Command IDs
#define ERROR_SCR_ID 1
#define INFO_SCR_ID 2
#define VOLUME_SCR_ID 3
#define CD_INFO_SCR_ID 4
#define CD_PLAYING_SCR_ID 5
#define RADIO_SCR_ID 6

// current screen
byte screenID = 0;

// play control icons
#define NO_ICON 0
#define PLAY_ICON 1
#define PAUSE_ICON 2

// source icons
#define NO_SOURCE 0
#define RADIO_SOURCE 1
#define CD_SOURCE 2

byte selectedSource = NO_SOURCE;
byte cdAvailable = 0;
byte sourcesDrawn = false;

// screen colors
#define RADIO_COLOR TFT_GREEN
#define CD_COLOR TFT_ORANGE
#define NO_CD_COLOR TFT_DARKGREY
#define VOLUME_COLOR TFT_WHITE
#define ERROR_COLOR TFT_RED
#define INFO_COLOR TFT_WHITE

#define BACKGROUND TFT_BLACK

#define PANEL_X 0
#define PANEL_Y 20
#define PANEL_W 159
#define PANEL_H 87

// NOTE - this value must fit python!!
#define FONT2_MAXCHARS 20

#define FONT2_H 16

// NOTE - this value must fit python!!
#define FONT4_MAXCHARS 12

#define FONT4_H 26

#define FONT6_H 48
#define FONT6_W 27

#define FONT8_W 55
#define FONT8_H 75

// display params
#define WIDTH 160
#define HEIGHT 128

// output consts
#define OUT_VOLUME_SCR_ID 'V'
#define OUT_BUTTON_ID 'B'
#define OUT_LOG_ID 'L'


byte icon = NO_ICON;
uint16_t iconColor = BACKGROUND;

uint16_t upDownButtonsColor = BACKGROUND;

uint16_t mainScreenColor = RADIO_COLOR;

// false until having received first complete screen info via serial
bool controllerRunning = false;

/********** LOGGING ******/
/**
   Send string over serial as log message
*/
void sendLog(char* msg) {
  Serial.write(FRAME_START);
  Serial.write(OUT_LOG_ID);
  Serial.print(msg);
  Serial.write(FRAME_END);
}

/**
   Log int over serial as char* message
*/
void logInt(int value) {
  char buffer[7];
  itoa(value, buffer, 10);
  sendLog(buffer);
}


/********** BUTTONS OUTPUT ******/
// pins for button 1 2 3 4
int buttonPins[4] = {4, 5, 3, 2};
// values from last check
boolean buttons[4] = {LOW, LOW, LOW, LOW};

void checkSendButtons() {
  // 0-based
  for (byte i = 0; i < 4; ++i) {
    checkSendButton(i);
  }
}

void checkSendButton(byte buttonIdx) {

  boolean value = digitalRead(buttonPins[buttonIdx]);
  if (buttons[buttonIdx] != value) {
    // transition
    if (value == HIGH) {
      // newly pressed
      sendButton(buttonIdx);
    }
    buttons[buttonIdx] = value;
  }
}

void sendButton(byte buttonIdx) {
  Serial.write(FRAME_START);
  Serial.write(OUT_BUTTON_ID);
  // 1-based
  Serial.write(buttonIdx + 1);
  Serial.write(FRAME_END);
}

/******* ANALOG VOLUME OUTPUT *******/
int volumeAnalogValue = 0;
byte volumeValue = 0;

// next time threshold for checking volume
static unsigned long volumeWaitMillis;


byte readVolume() {
  int newValue = analogRead(A0);
  // hysteresis
  if ((newValue < (volumeAnalogValue - 1)) || (newValue > (volumeAnalogValue + 1))) {
    volumeAnalogValue = newValue;
  }
  return map(volumeAnalogValue, 0, 1023, 0, 99);
}

void checkSendVolume() {
  if ( (long)( millis() - volumeWaitMillis ) >= 0) {
    byte newVolume = readVolume();
    if (newVolume != volumeValue) {
      volumeValue = newVolume;
      Serial.write(FRAME_START);
      Serial.write(OUT_VOLUME_SCR_ID);
      Serial.write(volumeValue);
      Serial.write(FRAME_END);
    }
    volumeWaitMillis += VOLUME_CHECK_PERIOD;
  }
}

/******** UTILS ***********/

/**
   Reading from serial structure to buf, size bytes
   checking START_FRAME, size, STOP_FRAME
   return: FALSE if all expected bytes not received within SERIAL_TIMEOUT or the (size+1)'th byte is not FRAME_END
*/
bool readStruct(char* buf, int size) {
  // receiving size bytes + STOP_FRAME
  byte readCount = Serial.readBytes(buf, size);
  if (readCount != size) {
    // timeout, did not receive enough bytes, error!
    return false;
  }
  // checking for STOP_FRAME
  byte stopFrame;
  readCount = Serial.readBytes(&stopFrame, 1);
  if (readCount < 1) {
    // timeout, did not receive enough bytes, error!
    return false;
  }
  // checking STOP FRAME
  // if different -> error!
  return (stopFrame == FRAME_END);
}

void clearWholeScreen() {
  tft.fillScreen(BACKGROUND);
  icon = NO_ICON;
  upDownButtonsColor = BACKGROUND;
  selectedSource = NO_SOURCE;
  sourcesDrawn = false;
}

void drawUpDown(uint16_t color) {
  if (color != upDownButtonsColor) {
    tft.fillTriangle(145, 10, 150, 3, 155, 10, color);
    tft.fillTriangle(145, 117, 150, 124, 155, 117, color);
    upDownButtonsColor = color;
  }
}

void clearUpDown() {
  drawUpDown(BACKGROUND);
}

#define ICON_X 3
#define ICON_Y 117
#define ICON_W 10
#define ICON_H 7
#define PAUSE_LINE_WIDTH 3

void clearIcon() {
  tft.fillRect(ICON_X, ICON_Y, ICON_W + 1, ICON_H + 1, BACKGROUND);
}


void drawIcon(byte newIcon, uint16_t color) {
  /*
    Serial.print(OUT_LOG_ID);
    Serial.print("icon: ");
    Serial.println(newIcon);
  */
  if (color != iconColor || icon != newIcon) {
    if (newIcon == PLAY_ICON) {
      // play icon
      clearIcon();
      tft.fillTriangle(ICON_X, ICON_Y, ICON_X, ICON_Y + ICON_H, ICON_X + ICON_W, ICON_Y + ICON_H / 2, color);
    } else if (newIcon == PAUSE_ICON) {
      // pause icon
      clearIcon();
      tft.fillRect(ICON_X, ICON_Y, PAUSE_LINE_WIDTH, ICON_H, color);
      tft.fillRect(ICON_X + ICON_W - PAUSE_LINE_WIDTH, ICON_Y, PAUSE_LINE_WIDTH, ICON_H, color);
    }
    icon = newIcon;
    iconColor = color;
  }
}

#define SOURCES_Y 1
#define RADIO_X 3
#define CD_X 30
#define SEL_BGND_COLOR TFT_DARKGREY



void drawSources(byte newSource, byte newCDAvailable) {
  if (!sourcesDrawn || newSource == NO_SOURCE) {
    drawRadio(0);
    drawCD(0, 0);
  }
  if (newSource != selectedSource) {
    if (newSource == RADIO_SOURCE || selectedSource == RADIO_SOURCE) {
      drawRadio(newSource == RADIO_SOURCE);
    }
    if (newSource == CD_SOURCE || selectedSource == CD_SOURCE) {
      drawCD(newSource == CD_SOURCE, newCDAvailable);
    }
    selectedSource = newSource;
  }
  // redrawing cd if needed
  if (newCDAvailable != cdAvailable) {
    drawCD(newSource == CD_SOURCE, newCDAvailable);
    cdAvailable = newCDAvailable;
  }
  sourcesDrawn = true;
}

void drawRadio(byte selected) {
  /*
    Serial.print(OUT_LOG_ID);
    Serial.print("Drawing RAD, selected:");
    Serial.println(selected);
  */
  if (selected)
    tft.setTextColor(RADIO_COLOR, SEL_BGND_COLOR);
  else
    tft.setTextColor(RADIO_COLOR, BACKGROUND);
  tft.drawString(" R ", RADIO_X, SOURCES_Y, 2);
  tft.setTextColor(mainScreenColor, BACKGROUND);
}

void drawCD(byte selected, byte isAvailable) {
  /*
      Serial.print(OUT_LOG_ID);
      Serial.print("Drawing CD, selected: ");
      Serial.print(selected);
      Serial.print(" isAvailable: ");
      Serial.println(isAvailable);
  */
  if (selected)
    tft.setTextColor(CD_COLOR, SEL_BGND_COLOR);
  else {
    uint16_t color;
    if (isAvailable)
      color = CD_COLOR;
    else
      color = NO_CD_COLOR;
    tft.setTextColor(color, BACKGROUND);
  }
  tft.drawString(" CD ", CD_X, SOURCES_Y, 2);
  // resetting the text color
  tft.setTextColor(mainScreenColor, BACKGROUND);
}

void clearPanel() {
  if (screenID == ERROR_SCR_ID)
    // this screen uses whole area
    clearWholeScreen();
  else
    // only the middle infopanel
    tft.fillRect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, BACKGROUND);
}
/******* VOLUME SCREEN *******/

#define VOLUME_X 20
#define VOLUME_Y 30


typedef struct volume_t {
  byte volume;
  byte icon;
  byte cdAvailable;
} volume_t;


volume_t volumeData = {0, 0, 0};

bool handleVolumeScreen() {
  volume_t newVolumeData;
  if (readStruct((char*) &newVolumeData, sizeof(volume_t))) {
    /*
      Serial.print(OUT_LOG_ID);
      Serial.print("Volumedata: volume: ");
      Serial.println(newVolumeData.volume);
      Serial.print(OUT_LOG_ID);
      Serial.print("icon: ");
      Serial.println(newVolumeData.icon);
      Serial.print(OUT_LOG_ID);
      Serial.print("cdAvailable: ");
      Serial.println(newVolumeData.cdAvailable);
    */
    showVolumeScreen(newVolumeData);
    return true;
  } else
    return false;
}

void showVolumeScreen(struct volume_t newVolumeData) {
  byte isNew;
  if (screenID != VOLUME_SCR_ID) {
    clearPanel();
    isNew = true;
  } else
    isNew = false;
  screenID = VOLUME_SCR_ID;
  drawUpDown(mainScreenColor);
  drawIcon(newVolumeData.icon, mainScreenColor);
  drawSources(selectedSource, newVolumeData.cdAvailable);
  drawVolumeNumbers(newVolumeData, isNew);
  memcpy(&volumeData, &newVolumeData, sizeof(volume_t));
}

void drawVolumeNumbers(struct volume_t newVolumeData, byte isNew) {
  byte volume = volumeData.volume;
  byte newVolume = newVolumeData.volume;
  if (isNew || newVolume != volume) {
    clearChangedVolumeChars(volume, newVolume);
    drawVolume(newVolume);
  }

}
void drawVolume(byte newVolume) {
  int xPos = VOLUME_X;
  if (newVolume < 10)
    // starting at second character
    xPos += FONT8_W;
  tft.setTextColor(VOLUME_COLOR);
  tft.drawNumber(newVolume, xPos, VOLUME_Y, 8);
  tft.setTextColor(mainScreenColor);
}

void clearChangedVolumeChars(byte volume, byte newVolume) {
  int xClearPos = VOLUME_X;
  if (newVolume / 10 == volume / 10)
    // clearing only last character if first digit not changed
    xClearPos += FONT8_W;
  // cleaning
  tft.fillRect(xClearPos, VOLUME_Y, 2 * FONT8_W, FONT8_H, BACKGROUND);
}

/******* ERROR/INFO SCREEN *******/

#define ERROR_Y 30
#define ERROR_X 1

typedef struct error_t {
  char line1[FONT2_MAXCHARS + 1];
  char line2[FONT2_MAXCHARS + 1];
  char line3[FONT2_MAXCHARS + 1];
} error_t;


bool handleErrorScreen() {
  return handleErrorScreen("Error", ERROR_COLOR);
}

bool handleInfoScreen() {
  return handleErrorScreen("Info", INFO_COLOR);
}


bool handleErrorScreen(char* label, uint16_t color) {
  error_t errorData;
  if (readStruct((char*) &errorData, sizeof(error_t))) {
    /*
      sendLog(label);
      sendLog(": line1: ");
      sendLog(errorData.line1);
      sendLog("\n");
    */
    showErrorScreen(errorData, label, color);
    return true;
  } else
    return false;
}

void showErrorScreen(struct error_t errorData, char* label, uint16_t color) {
  clearWholeScreen();
  screenID = ERROR_SCR_ID;
  tft.setTextColor(color);
  // headline
  tft.drawCentreString(label, WIDTH / 2, 1, 4);
  // 3 lines of text
  tft.drawString(errorData.line1, ERROR_X, ERROR_Y, 2);
  tft.drawString(errorData.line2, ERROR_X, ERROR_Y + FONT2_H, 2);
  tft.drawString(errorData.line3, ERROR_X, ERROR_Y + 2 * FONT2_H, 2);
  tft.setTextColor(mainScreenColor);
}


/******* RADIO SCREEN *******/

#define R_STATION_Y 30

#define R_TITLE_Y 60

typedef struct radio_t {
  char station1[FONT4_MAXCHARS + 1];
  char station2[FONT4_MAXCHARS + 1];
  char title1[FONT2_MAXCHARS + 1];
  char title2[FONT2_MAXCHARS + 1];
  byte icon;
  byte cdAvailable;
} radio_t;

radio_t radioData = {"", "", "", "", NO_ICON, 0};

bool handleRadioScreen() {
  radio_t newRadioData;
  if (readStruct((char*) &newRadioData, sizeof(radio_t))) {
    /*
      Serial.print(OUT_LOG_ID);
      Serial.print("radiodata: station1: ");
      Serial.println(newRadioData.station1);
      Serial.print(OUT_LOG_ID);
      Serial.print("station2: ");
      Serial.println(newRadioData.station2);
      Serial.print(OUT_LOG_ID);
      Serial.print("title1: ");
      Serial.println(newRadioData.title1);
      Serial.print(OUT_LOG_ID);
      Serial.print("line2: ");
      Serial.println(newRadioData.title2);
      Serial.print(OUT_LOG_ID);
      Serial.print("icon: ");
      Serial.println(newRadioData.icon);
      Serial.print(OUT_LOG_ID);
      Serial.print("cdAvailable: ");
      Serial.println(newRadioData.cdAvailable);
    */
    showRadioScreen(newRadioData);
    return true;
  } else
    return false;
}

void showRadioScreen(struct radio_t newRadioData) {
  byte isNew;
  if (screenID != RADIO_SCR_ID) {
    clearPanel();
    switchGlobalsToRadio();
    isNew = true;
  } else
    isNew = false;

  drawUpDown(mainScreenColor);
  drawIcon(newRadioData.icon, mainScreenColor);
  drawSources(RADIO_SOURCE, newRadioData.cdAvailable);
  drawRadioLines(newRadioData, isNew);
  memcpy(&radioData, &newRadioData, sizeof(radio_t));
}

void drawRadioLines(struct radio_t newRadioData, byte isNew) {
  boolean redraw = isNew
                   || strcmp(newRadioData.station1, radioData.station1)
                   || strcmp(newRadioData.station2, radioData.station2)
                   || strcmp(newRadioData.title1, radioData.title1)
                   || strcmp(newRadioData.title2, radioData.title2);
  /*
    Serial.print(OUT_LOG_ID);
    Serial.println("Redrawing radio");
  */
  if (redraw) {
    clearPanel();
    byte titleY = R_TITLE_Y;
    boolean station2Drawn = false;
    drawStation(newRadioData.station1, 0);
    if (newRadioData.station2[0] != '\0') {
      // second station line available
      drawStation(newRadioData.station2, 1);
      station2Drawn = true;
      // title lines moved downward by station line height
      titleY += FONT4_H;
    }
    drawRTitle(newRadioData.title1, 0, titleY);
    if (!station2Drawn) {
      // no second station line => space enough for the second title line
      drawRTitle(newRadioData.title2, 1, titleY);
    }
  }
}

void drawStation(char * station, byte index) {
  byte posY = R_STATION_Y + (index * FONT4_H);
  tft.drawCentreString(station, WIDTH / 2, posY, 4);
}

void drawRTitle(char * title, byte index, byte posY) {
  posY = posY + (index * FONT2_H);
  tft.drawCentreString(title, WIDTH / 2, posY, 2);
}

void switchGlobalsToRadio() {
  screenID = RADIO_SCR_ID;
  mainScreenColor = RADIO_COLOR;
}

/******* CD PLAYING SCREEN *******/

#define LABELS_Y 30

#define TRACKNB_X 40
#define TRACKNB_Y 50

#define TRACKS_X 120
#define TRACKS_Y TRACKNB_Y


typedef struct cd_t {
  byte trackNb;
  byte tracks;
  byte icon;
} cd_t;

cd_t cdData = {0, 0, NO_ICON};

bool handleCDPlayingScreen() {
  cd_t newCDData;
  if (readStruct((char*) &newCDData, sizeof(cd_t))) {
    /*
      Serial.print(OUT_LOG_ID);
      Serial.print("CDdata: trackNb: ");
      Serial.println(newCDData.trackNb);
      Serial.print(OUT_LOG_ID);
      Serial.print("tracks: ");
      Serial.println(newCDData.tracks);
      Serial.print(OUT_LOG_ID);
      Serial.print("icon: ");
      Serial.println(newCDData.icon);
    */
    showCDPlayingScreen(newCDData);
    return true;
  } else
    return false;
}

void showCDPlayingScreen(struct cd_t newCDData) {
  byte isNew;
  if (screenID != CD_PLAYING_SCR_ID) {
    isNew = true;
    clearPanel();
    switchGlobalsToCDPlaying();
  } else
    isNew = false;

  drawUpDown(mainScreenColor);
  drawSources(CD_SOURCE, true);
  drawIcon(newCDData.icon, mainScreenColor);
  drawCDTracks(newCDData, isNew);
  memcpy(&cdData, &newCDData, sizeof(cd_t));
}

void drawCDTracks(struct cd_t newCDData, byte isNew) {
  tft.setTextColor(mainScreenColor, BACKGROUND);
  if (isNew) {
    drawLabels();
  }
  if (isNew || newCDData.trackNb != cdData.trackNb)
    drawTrackNb(newCDData.trackNb);

  if (isNew || newCDData.tracks != cdData.tracks)
    drawTracks(newCDData.tracks);
}

void drawTrackNb(byte trackNb) {
  drawCDValue(trackNb, TRACKNB_X, TRACKNB_Y);
}

void drawTracks(byte tracks) {
  drawCDValue(tracks, TRACKS_X, TRACKS_Y);
}

void drawLabels() {
  tft.drawCentreString("track", TRACKNB_X, LABELS_Y, 2);
  tft.drawCentreString("total", TRACKS_X, LABELS_Y, 2);
}

void drawCDValue(byte value, byte x, byte y) {
  tft.fillRect(x - FONT6_W, y, 2 * FONT6_W, FONT6_H, BACKGROUND);
  char buf[4] = {'\0'};
  itoa(value, buf, 10);
  tft.drawCentreString(buf, x, y, 6);
}


void switchGlobalsToCDPlaying() {
  screenID = CD_PLAYING_SCR_ID;
  mainScreenColor = CD_COLOR;
}

/******* CD INFO SCREEN *******/

#define CD_INFO_X 80
#define CD_INFO_Y 50

typedef struct cd_info_t {
  char text[FONT4_MAXCHARS + 1];
} cd_info_t;

cd_info_t cdInfoData = {""};


bool handleCDInfoScreen() {
  cd_info_t newCDInfoData;
  if (readStruct((char*) &newCDInfoData, sizeof(cd_info_t))) {
    /*
      Serial.print(OUT_LOG_ID);
      Serial.print("CDInfoData: text: ");
      Serial.println(newCDInfoData.text);
    */
    showCDInfoScreen(newCDInfoData);
    return true;
  } else
    return false;
}

void showCDInfoScreen(struct cd_info_t newCDInfoData) {
  byte isNew;
  if (screenID != CD_INFO_SCR_ID) {
    isNew = true;
    clearPanel();
    switchGlobalsToCDLoading();
  } else
    isNew = false;

  drawUpDown(mainScreenColor);
  drawSources(CD_SOURCE, true);
  drawIcon(PAUSE_ICON, mainScreenColor);
  drawCDInfo(newCDInfoData, isNew);
  memcpy(&cdInfoData, &newCDInfoData, sizeof(cd_info_t));
}

void drawCDInfo(struct cd_info_t newCDInfoData, byte isNew) {
  tft.setTextColor(mainScreenColor, BACKGROUND);
  if (isNew || strcmp(newCDInfoData.text, cdInfoData.text)) {
    tft.fillRect(0, CD_INFO_Y, WIDTH, FONT4_H, BACKGROUND);
    tft.drawCentreString(newCDInfoData.text, CD_INFO_X, CD_INFO_Y, 4);
  }
}


void switchGlobalsToCDLoading() {
  screenID = CD_INFO_SCR_ID;
  mainScreenColor = CD_COLOR;
}

/************* INITIAL SCREEN ************/
void showInitialScreen() {
  tft.setTextColor(INFO_COLOR, BACKGROUND);
  tft.drawCentreString("Starting...", 80, 50, 4);
}

bool handleCommand(byte commandID) {
  switch (commandID) {
    case VOLUME_SCR_ID: return handleVolumeScreen();
    case RADIO_SCR_ID: return handleRadioScreen();
    case CD_PLAYING_SCR_ID: return handleCDPlayingScreen();
    case CD_INFO_SCR_ID: return handleCDInfoScreen();
    case INFO_SCR_ID: return handleInfoScreen();
    case ERROR_SCR_ID: return handleErrorScreen();
    // unknown commandID
    default: return false;
  }

}

/**
 * Called when new serial data available
 * Does not return until command is fully completed or the message was not received/parsed correctly
 * return:  FALSE - message corrupted/not recognized correctly
 *          TRUE - message received correctly, processed
 */
bool checkAndHandleMsg() {
  // incoming data
  int startFrame = Serial.read();
  //  sendLog("FRAME_START ASCII:");
  //  logInt(startFrame);
  // first byte must be FRAME_START
  if (startFrame != FRAME_START) {
    // not frame start, returning
    return false;
  }
  // read START_FRAME, now command ID byte
  byte commandID;
  // read with timeout
  byte readCount = Serial.readBytes(&commandID, 1);
  if (readCount == 1) {
    //    sendLog("SCREEN_ID ASCII:");
    //    logInt(commandID);
    // did receive one byte within timeout
    return handleCommand(commandID);
  } else
    return false;
}

/********** MAIN *********/
void setup(void) {
  tft.init();
  tft.setRotation(3);
  tft.setTextSize(1);
  volumeWaitMillis = millis() + VOLUME_CHECK_PERIOD;  // initial setup
  controllerRunning = false;

  Serial.begin(4800);
  Serial.setTimeout(SERIAL_TIMEOUT);
  tft.fillScreen(BACKGROUND);
  showInitialScreen();
}

void loop() {
  if (Serial.available()) {
    // incoming data
    controllerRunning |= checkAndHandleMsg();
  }

  // volume/button info is sent over serial ONLY AFTER the controller shows it is communicating - after having received its first complete command
  if (controllerRunning) {
    // the controller has sent a complete command correctly - is running
    // sending volume if changed
    checkSendVolume();
    // sending button if newly pressed
    checkSendButtons();
  }
}
