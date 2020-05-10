library(ggplot2)
library(dplyr)
library(tidyr)
library(grid)
#library(lubridate)
#library(multcomp)
library(lme4)
library(lmerTest)
library(sjPlot)




bw <- read.csv("../data/buckwheat_fullData.csv", header=T)

bw <- bw %>% 
  mutate(Observation = paste(Date, Pair, Size))

nectar.summary <- bw %>%
  group_by(Observation) %>%
  summarise(avgSugarContent = mean(sugarContPerFlow))

plant.summary <- distinct(select(bw,-sugarContPerFlow,-X))

bw <- inner_join(nectar.summary,plant.summary, by="Observation")

bw <- bw %>% 
  mutate(log.fl.density = log(flowerDensity)) %>%
  mutate(log.sugar = log(avgSugarContent)) %>%
  mutate(log.fl.area = log(flowerArea)) %>%
  mutate(log.infl.obs = log(infl_Obs)) %>%
  mutate(log.fpi = log(aveFlowPerInfl))



bw %>% 
  ggplot(aes(x=Date,y=Honeybees,col=Size)) + geom_point()
heightplot <- bw %>% 
  ggplot(aes(x=Size,y=height,fill=Size)) + geom_boxplot() + 
  ylab("Plant height (m)") +
  guides(fill = "none")
efficiencyplot <- bw %>% 
  ggplot(aes(x=Size,y=flowerDensity,fill=Size)) + geom_boxplot() + 
  ylab("Flower density (proportion)") +
  guides(fill = "none")
rewardplot <- bw %>% 
  ggplot(aes(x=Size,y=avgSugarContent,fill=Size)) + geom_boxplot() + 
  ylab("Sugar content/flower") +
  guides(fill = "none")
potentialplot <- bw %>% 
  ggplot(aes(x=Size,y=flowerArea,fill=Size)) + geom_boxplot() + 
  ylab("Total flower area")

grid.newpage()
grid.draw(cbind(ggplotGrob(heightplot), ggplotGrob(efficiencyplot),ggplotGrob(rewardplot), ggplotGrob(potentialplot), size = "last"))



model.null.hb <- glmer(Honeybees ~ 1 + (1|Date/Pair/Size), 
                        family="poisson", data=bw)
summary(model.null.hb)
deviance(model.null.hb)/df.residual(model.null.hb)
1-pchisq(deviance(model.null.hb),df.residual(model.null.hb))



model.size.hb <- glmer(Honeybees ~ Size + (1|Date/Pair/Size), 
                        family="poisson", data=bw)
summary(model.size.hb)
deviance(model.size.hb)/df.residual(model.size.hb)
1-pchisq(deviance(model.size.hb),df.residual(model.size.hb))



ggplot(bw, aes(x=Size, y=Honeybees, group=Pair, color=Size))+
  geom_line(color="gray")+
  geom_point()+
  facet_grid(.~Date)+
  theme_classic()



model.full.hb <- glmer(Honeybees ~ height + log.fl.density + log.sugar + log.fl.area + (1|Date/Pair/Size), 
                        family="poisson", data=bw)
summary(model.full.hb)
deviance(model.full.hb)/df.residual(model.full.hb)
1-pchisq(deviance(model.full.hb),df.residual(model.full.hb))
heightplot <- plot_model(model.full.hb, 
                         type="eff", terms="height",
                         show.data=T, title="", 
                         axis.labels = c("Height", "Honeybees"),
                         axis.lim = c(0,60))
efficiencyplot <- plot_model(model.full.hb, 
                             type="eff", terms="log.fl.density",
                             show.data=T, title="", 
                             axis.labels = c("Flower density", "Honeybees"),
                             axis.lim = c(0,60))
rewardplot <- plot_model(model.full.hb, 
                         type="eff", terms="log.sugar",
                         show.data=T, title="", 
                         axis.labels = c("Sugar", "Honeybees"),
                         axis.lim = c(0,60))
potentialplot <- plot_model(model.full.hb, 
                            type="eff", terms="log.fl.area",
                            show.data=T, title="", 
                            axis.labels = c("Flower area (m^2)", "Honeybees"),
                         axis.lim = c(0,60))

grid.newpage()
grid.draw(cbind(ggplotGrob(heightplot), 
                ggplotGrob(efficiencyplot),
                ggplotGrob(rewardplot), 
                ggplotGrob(potentialplot), size = "last"))

plot_model(model.full.hb, type="est")
plot_model(model.full.hb, type="diag", grid=T)




model.size.hb <- glmer(Honeybees ~ offset(log.infl.obs) + Size + (1|Date/Pair/Size), 
                        family="poisson", data=bw)
summary(model.size.hb)
deviance(model.size.hb)/df.residual(model.size.hb)
1-pchisq(deviance(model.size.hb),df.residual(model.size.hb))



model.full.hb <- glmer(Honeybees ~ height + offset(log.infl.obs) + log.fpi + log.sugar + log.fl.area + (1|Date/Pair/Size), 
                        family="poisson", data=bw)
summary(model.full.hb)
deviance(model.full.hb)/df.residual(model.full.hb)
1-pchisq(deviance(model.full.hb),df.residual(model.full.hb))
heightplot <- plot_model(model.full.hb, 
                         type="eff", terms="height",
                         show.data=T, title="", 
                         axis.labels = c("Height", "Honeybees"),
                         axis.lim = c(0,45))
efficiencyplot <- plot_model(model.full.hb, 
                             type="eff", terms="log.fpi",
                             show.data=T, title="", 
                             axis.labels = c("Flowers per Inflorescence", "Honeybees"),
                             axis.lim = c(0,45))
rewardplot <- plot_model(model.full.hb, 
                         type="eff", terms="log.sugar",
                         show.data=T, title="", 
                         axis.labels = c("Sugar", "Honeybees"),
                         axis.lim = c(0,45))
potentialplot <- plot_model(model.full.hb, 
                            type="eff", terms="log.fl.area",
                            show.data=T, title="", 
                            axis.labels = c("Flower area (m^2)", "Honeybees"),
                         axis.lim = c(0,45))

grid.newpage()
grid.draw(cbind(ggplotGrob(heightplot), 
                ggplotGrob(efficiencyplot),
                ggplotGrob(rewardplot), 
                ggplotGrob(potentialplot), size = "last"))

plot_model(model.full.hb, type="est")
plot_model(model.full.hb, type="diag", grid=T)


# bw$logHoneybees = log(bw$Honeybees+1)
# bw$log.density = log(bw$flowerDensity)
# bw$log.sugar = log(bw$avgSugarContent)
# bw$log.area = log(bw$flowerArea)

# lmodel.full.hb <- lmer(logHoneybees ~ height + log.density +
#                         log.sugar + log.area + (1|Date), 
#                        data=bw)

# summary(lmodel.full.hb)



# plot_model(lmodel.full.hb, type="eff", terms="height",show.data=T)
# plot_model(lmodel.full.hb, type="eff", terms="log.density",show.data=T)
# plot_model(lmodel.full.hb, type="eff", terms="log.sugar",show.data=T)
# plot_model(lmodel.full.hb, type="eff", terms="log.area",show.data=T)



# plot_model(lmodel.full.hb, type="diag")
