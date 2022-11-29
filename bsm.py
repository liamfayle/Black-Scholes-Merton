import scipy
import scipy.stats
from scipy.stats import norm
import numpy as np

'''
    TODO
'''
class BsmOption:
    def __init__(self, isLong, Type, S, K, T, r, sigma=-1.0, value=-1.0, q=0.0):
        '''
        NOTE Only sigma OR value should be passed to the constructor

        isLong -> Long / short          [bool]          [False]         Short the option
        Type -> 'P' or 'C'              [Char]          ['P']           Put option
        S -> Underlying Price           [$]             [100]           100$ Underlying                 \n
        K -> Strike                     [$]             [110]           110$ Strike                     \n
        T -> Time until expiration      [Decimal]       [20]            20 DTE                          \n
        r -> Risk free rate             [Decimal]       [0.01]          1% RFR Continous yield          \n
        sigma -> Volatility             [Decimal]       [0.45]          45% Vol                         \n
        value -> Option Price           [$]             [1.56]          1.56$                           \n
        q -> Dividend Value             [Decimal]       [0.01]          1% Continous Div yield            
        '''
        self.isLong = isLong
        self.Type = Type.upper()
        self.S = S 
        self.K = K
        self.T = T / 365
        self.r = r
        self.q = q
        self.sigma = sigma
        self.value = value

        #Get sigma from market price
        if (sigma < 0.0):
            self.NewtonRaphson()

        if (value < 0.0):
            self.value = self.price()

        if (type(self.isLong) is not bool or type(self.Type) is not str):
            raise ValueError('Incorrect types for constructor')
        if ( not (self.Type == 'P' or self.Type == 'C')):
            raise ValueError('Must be "P" or "C"')

    
    @staticmethod
    def N(x):
        return norm.cdf(x)

    @staticmethod
    def N_prime(x):
        return norm.pdf(x)

    @property
    def params(self):
        return {'isLong': self.isLong,
                'Type': self.Type,
                'S': self.S,
                'K': self.K,
                'T': self.T,
                'r': self.r,
                'sigma': self.sigma,
                'value': self.value,
                'q': self.q}


    def NewtonRaphson(self):
        '''
        https://en.wikipedia.org/wiki/Newton%27s_method
        Get approximate sigma using Newton Raphson Method for root finding
        Iterates until 0.1% accuracy
        '''
        sigma_i_1 = 0
        sigma_i = 1 #arbitrary guess
        self.setSigma(sigma_i)
        while 1:
            sigma_i_1 = sigma_i - ((self.price() - self.value) / (self.vega()))
            sigma_i = sigma_i_1
            self.setSigma(sigma_i)

            if ( abs((self.value - self.price()) /  self.value) < 0.001 ):
                self.setSigma(abs(sigma_i))
                return


    def d1(self):
        return (np.log(self.S/self.K) + ((self.r -self.q + self.sigma**2/2)*self.T)) / (self.sigma*np.sqrt(self.T))
    
    def d2(self):
        return self.d1() - self.sigma*np.sqrt(self.T)
    
    def _call_value(self):
        call_value = self.S*np.exp(-self.q*self.T)*self.N(self.d1()) - self.K*np.exp(-self.r*self.T) * self.N(self.d2())
        if (self.isLong):
            return call_value
        return -1 * call_value
                    
    def _put_value(self):
        put_value = (self.K*np.exp(-self.r*self.T) * self.N(-self.d2())) - (self.S*np.exp(-self.q*self.T)*self.N(-self.d1()))
        if (self.isLong):
            return put_value
        return -1 * put_value

    def delta(self):
        '''
        Return Delta Greek Value \n
        '''
        delta = 0
        if self.Type == 'C':
            delta = np.exp(-self.q * self.T) * self.N(self.d1())
        if self.Type == 'P':
            delta = -np.exp(-self.q * self.T) * self.N(-self.d1())

        if (self.isLong):
            return delta

        return delta * -1
        
        

    def gamma(self):
        '''
        Return Gamma Greek Value \n
        '''
        gamma =  np.exp(-self.q * self.T) * ((self.N_prime(self.d1())) / (self.S * self.sigma * np.sqrt(self.T)))

        if (self.isLong):
            return gamma

        return gamma * -1

    def vega(self):
        '''
        Return Delta Greek Value \n
        '''
        vega = self.S * np.exp(-self.q * self.T) * self.N_prime(self.d1()) * np.sqrt(self.T)

        vega /= 100 #adjustment factor to single share

        if (self.isLong):
            return vega

        return vega * -1


    def theta(self):
        '''
        Return theta Greek Value \n
        '''
        theta = 0
        if self.Type == 'C':
            theta = (-np.exp(-self.q * self.T) * ((self.S * self.N_prime(self.d1()) * self.sigma)/(2 * np.sqrt(self.T)))) - (self.r * self.K * np.exp(-self.r * self.T) * self.N(self.d2())) + (self.q * self.S * np.exp(-self.q * self.T) * self.N(self.d1()))
        if self.Type == 'P':
            theta = (-np.exp(-self.q * self.T) * ((self.S * self.N_prime(self.d1()) * self.sigma)/(2 * np.sqrt(self.T)))) + (self.r * self.K * np.exp(-self.r * self.T) * self.N(-self.d2())) - (self.q * self.S * np.exp(-self.q * self.T) * self.N(-self.d1()))

        theta /= 365

        if (self.isLong):
            return theta 

        return theta * -1


    def rho(self):
        '''
        Return rho Greek Value \n
        '''
        rho = 0
        if self.Type == 'C':
            rho = self.K * self.T * np.exp(-self.r * self.T) * self.N(self.d2())
        if self.Type == 'P':
            rho = -self.K * self.T * np.exp(-self.r * self.T) * self.N(-self.d2())
        
        rho /= 100 #adjustment factor to single share

        if (self.isLong):
            return rho
        
        return rho * -1
    
    def price(self):
        '''
        Return price of option \n
        '''
        if self.Type == 'C':
            return self._call_value()
        if self.Type == 'P':
            return self._put_value() 



    def setSpot(self, spot):
        '''
        Sets new spot price
        '''
        self.S = spot

    def setDTE(self, DTE):
        '''
        Sets new DTE
        '''
        self.T = DTE / 365

    def setSigma(self, sigma):
        '''
        Sets new volatility value
        '''
        self.sigma = sigma



'''
    TODO
        >Add selector for individual option
            *Can then call indivudal update functions that option
        >Bug with greeks (delta & gamma) when init with market price rather than vol
'''
class OptionPosition:
    def __init__(self):
        self.legs = []
        self.shares = 0
        pass


    def addLegs(self, options):
        '''
        option -> BSM option object LIST \n
        adds option leg to position
        '''
        for option in options:
            self.legs.append(option)

    def addShares(self, shares):
        '''
        shares -> Num shares \n
        adds shares to position
        '''
        self.shares += shares

    def removeShares(self, shares):
        '''
        shares -> Num shares \n
        removes shares from position
        '''
        self.shares -= shares

    def removeLeg(self, option):
        '''
        option -> BSM option object to be removed
        Removes leg from position
        '''
        try:
            self.legs.remove(option)
        except Exception as e:
            print(e)

    def getLeg(self, index):
        '''
        Get leg at specified index
        '''
        if (index > len(self.legs)):
            raise Exception("Cannot get index greater than size")

        return self.legs[index]

    def price(self):
        '''
        Returns current theoretical price of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.price()
        return value

    def delta(self):
        '''
        Returns current delta of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.delta()
        value += (self.shares/100)
        return value

    def gamma(self):
        '''
        Returns current gamma of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.gamma()
        return value

    def vega(self):
        '''
        Returns current vega of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.vega()
        return value

    def theta(self):
        '''
        Returns current theta of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.theta()
        return value

    def rho(self):
        '''
        Returns current rho of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.rho()
        return value

    def sigma(self):
        '''
        Returns average sigma of position
        '''
        value = 0
        for leg in self.legs:
            value += leg.sigma
        return value / len(self.legs)


    def updateDTE(self, DTE):
        '''
        Updates DTE of !ALL! options in position
        '''
        for leg in self.legs:
            leg.setDTE(DTE)

    def updateSigma(self, DTE):
        '''
        Updates DTE of !ALL! options in position
        '''
        for leg in self.legs:
            leg.setSigma(DTE)

    def updateSpot(self, spot):
        '''
        Updates Spot price of !ALL! options in position
        '''
        for leg in self.legs:
            leg.setSpot(spot)

    


    




position = OptionPosition()
option = BsmOption(True, 'C', 15.5, 15, 53, 0.05, sigma=0.636)

print("Price = " + str(option.price()))
print("Sigma = " + str(option.sigma))
print("Delta = " + str(option.delta()))
print("Gamma = " + str(option.gamma()))
print("Vega  = " + str(option.vega()))
print("Theta = " + str(option.theta()))
print("Rho   = " + str(option.rho()))

'''put = BsmOption(False, 'P', 15.00, 15, 53, 0.01, value=1.68)
position.addLegs([call, put])
print("Price = " + str(position.price()))
print("Sigma = " + str(position.sigma()))
print("Delta = " + str(position.delta()))
print("Gamma = " + str(position.gamma()))
print("Vega  = " + str(position.vega()))
print("Theta = " + str(position.theta()))
print("Rho   = " + str(position.rho()))'''